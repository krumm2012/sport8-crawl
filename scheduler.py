#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务调度器
支持：
1. 定时执行数据爬取（auto_crawl_with_ocr.py）
2. 定时执行数据同步（integrations/sport8_sync.py）
3. Cron 风格的调度配置
"""

import os
import sys
import time
import subprocess
import logging
from datetime import datetime, time as dt_time
from pathlib import Path
from typing import Optional

# 配置日志
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f'scheduler_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# 脚本路径
BASE_DIR = Path(__file__).parent
CRAWL_SCRIPT = BASE_DIR / "auto_crawl_with_ocr.py"
SYNC_SCRIPT = BASE_DIR / "integrations" / "sport8_sync.py"

# 默认调度配置
CRAWL_SCHEDULE = {
    "enabled": os.getenv("CRAWL_ENABLED", "true").lower() == "true",
    "times": ["08:00", "12:00", "18:00"],  # 每天执行时间
    "interval": None,  # 如果设置，则按间隔执行（秒）
}

SYNC_SCHEDULE = {
    "enabled": os.getenv("SYNC_ENABLED", "true").lower() == "true",
    "loop_mode": True,  # 使用循环模式（07:00-23:00 每15分钟）
    "interval": 15 * 60,  # 15分钟
    "window_start": 7,  # 07:00
    "window_end": 23,  # 23:00
}


def run_crawl():
    """执行数据爬取"""
    if not CRAWL_SCRIPT.exists():
        logger.error(f"爬取脚本不存在: {CRAWL_SCRIPT}")
        return False
    
    logger.info("=" * 70)
    logger.info("开始执行数据爬取任务")
    logger.info("=" * 70)
    
    try:
        # 在 Docker 中需要使用 headless 模式
        env = os.environ.copy()
        env["HEADLESS"] = "true"  # 告诉脚本使用 headless 模式
        
        result = subprocess.run(
            [sys.executable, str(CRAWL_SCRIPT)],
            cwd=str(BASE_DIR),
            env=env,
            capture_output=True,
            text=True,
            timeout=600  # 10分钟超时
        )
        
        if result.returncode == 0:
            logger.info("✓ 数据爬取成功完成")
            if result.stdout:
                logger.info(f"输出: {result.stdout[-500:]}")  # 只显示最后500字符
            return True
        else:
            logger.error(f"✗ 数据爬取失败 (退出码: {result.returncode})")
            if result.stderr:
                logger.error(f"错误: {result.stderr[-500:]}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("✗ 数据爬取超时（超过10分钟）")
        return False
    except Exception as e:
        logger.error(f"✗ 执行爬取任务时出错: {e}", exc_info=True)
        return False


def run_sync_once():
    """执行单次数据同步（不使用 --loop）"""
    if not SYNC_SCRIPT.exists():
        logger.error(f"同步脚本不存在: {SYNC_SCRIPT}")
        return False
    
    logger.info("=" * 70)
    logger.info("开始执行数据同步任务（单次）")
    logger.info("=" * 70)
    
    try:
        result = subprocess.run(
            [sys.executable, str(SYNC_SCRIPT)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode == 0:
            logger.info("✓ 数据同步成功完成")
            if result.stdout:
                logger.info(f"输出: {result.stdout[-500:]}")
            return True
        else:
            logger.error(f"✗ 数据同步失败 (退出码: {result.returncode})")
            if result.stderr:
                logger.error(f"错误: {result.stderr[-500:]}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("✗ 数据同步超时（超过5分钟）")
        return False
    except Exception as e:
        logger.error(f"✗ 执行同步任务时出错: {e}", exc_info=True)
        return False


def start_sync_loop():
    """启动同步任务的循环模式（独立进程）"""
    if not SYNC_SCRIPT.exists():
        logger.error(f"同步脚本不存在: {SYNC_SCRIPT}")
        return None
    
    logger.info("启动数据同步循环任务（独立进程）...")
    
    try:
        # 启动独立进程，不等待完成
        process = subprocess.Popen(
            [sys.executable, str(SYNC_SCRIPT), "--loop"],
            cwd=str(BASE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info(f"✓ 同步循环任务已启动 (PID: {process.pid})")
        return process
    except Exception as e:
        logger.error(f"✗ 启动同步循环任务失败: {e}", exc_info=True)
        return None


def is_time_in_window(current_time: dt_time, start_hour: int, end_hour: int) -> bool:
    """检查当前时间是否在时间窗口内"""
    current_hour = current_time.hour
    return start_hour <= current_hour < end_hour


def should_run_crawl() -> bool:
    """判断是否应该执行爬取任务"""
    if not CRAWL_SCHEDULE["enabled"]:
        return False
    
    now = datetime.now()
    current_time = now.time()
    
    # 如果设置了间隔时间，按间隔执行
    if CRAWL_SCHEDULE.get("interval"):
        # 这里简化处理，实际可以使用更复杂的调度逻辑
        return True
    
    # 按指定时间点执行
    scheduled_times = CRAWL_SCHEDULE.get("times", [])
    for time_str in scheduled_times:
        try:
            hour, minute = map(int, time_str.split(":"))
            scheduled = dt_time(hour, minute)
            # 允许5分钟的误差
            if abs((current_time.hour * 60 + current_time.minute) - 
                   (scheduled.hour * 60 + scheduled.minute)) <= 5:
                return True
        except ValueError:
            logger.warning(f"无效的时间格式: {time_str}")
    
    return False


def should_run_sync() -> bool:
    """判断是否应该执行同步任务（单次模式）"""
    if not SYNC_SCHEDULE["enabled"]:
        return False
    
    # 如果使用循环模式，不需要在这里调度（由独立进程处理）
    if SYNC_SCHEDULE.get("loop_mode"):
        return False
    
    # 单次模式：可以在这里添加调度逻辑
    return False


def main():
    """主调度循环"""
    logger.info("=" * 70)
    logger.info("Sport8 爬虫定时任务调度器启动")
    logger.info(f"工作目录: {BASE_DIR}")
    logger.info(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    # 检查脚本是否存在
    if not CRAWL_SCRIPT.exists():
        logger.warning(f"爬取脚本不存在，将跳过爬取任务: {CRAWL_SCRIPT}")
    if not SYNC_SCRIPT.exists():
        logger.warning(f"同步脚本不存在，将跳过同步任务: {SYNC_SCRIPT}")
    
    # 如果同步任务使用循环模式，启动独立进程
    sync_process = None
    if SYNC_SCHEDULE.get("enabled") and SYNC_SCHEDULE.get("loop_mode"):
        sync_process = start_sync_loop()
        if sync_process:
            logger.info("同步任务已在独立进程中运行（循环模式）")
    
    # 主循环（只处理爬取任务）
    last_crawl_time = None
    
    try:
        while True:
            try:
                now = datetime.now()
                
                # 检查是否需要执行爬取任务
                if should_run_crawl():
                    # 避免重复执行（同一分钟内只执行一次）
                    if last_crawl_time is None or (now - last_crawl_time).total_seconds() > 60:
                        run_crawl()
                        last_crawl_time = now
                
                # 检查同步进程是否还在运行
                if sync_process and sync_process.poll() is not None:
                    logger.warning(f"同步进程已退出 (退出码: {sync_process.returncode})，尝试重启...")
                    sync_process = start_sync_loop()
                
                # 等待一段时间再检查（避免 CPU 占用过高）
                time.sleep(60)  # 每分钟检查一次
                
            except KeyboardInterrupt:
                logger.info("收到中断信号，正在退出...")
                break
            except Exception as e:
                logger.error(f"调度循环出错: {e}", exc_info=True)
                time.sleep(60)  # 出错后等待1分钟再继续
    finally:
        # 清理：停止同步进程
        if sync_process:
            logger.info("正在停止同步进程...")
            sync_process.terminate()
            try:
                sync_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning("同步进程未在10秒内退出，强制终止...")
                sync_process.kill()


if __name__ == "__main__":
    # 如果传入了参数，执行单次任务
    if len(sys.argv) > 1:
        if sys.argv[1] == "crawl":
            run_crawl()
        elif sys.argv[1] == "sync":
            run_sync_once()
        else:
            print(f"未知参数: {sys.argv[1]}")
            print("用法: python3 scheduler.py [crawl|sync]")
            sys.exit(1)
    else:
        # 无参数时进入调度循环
        main()

