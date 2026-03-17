#!/usr/bin/env python3
"""
Sport8 双地址同步脚本
同时同步到 bakewell.cloud 和 124.223.13.170
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from integrations.sport8_sync import (
    Sport8Client, sync_orders, sync_locked_bookings, 
    parse_cli_args, load_config_file, DEFAULT_BASE_URL,
    DEFAULT_USERNAME, DEFAULT_PASSWORD, DEFAULT_VENUE_ID,
    LOCKED_STATUSES, PAID_STATUSES, COURT_ID_MAP,
    EXPORT_DIR, ensure_state_dir, load_state, save_state,
    parse_orders_files, parse_bookings_files, resolve_court_id
)


def sync_to_target(args, config, target_config, state_key_prefix=""):
    """同步到单个目标"""
    target_name = target_config.get("name", "unknown")
    base_url = target_config.get("base_url", config.get("base_url", DEFAULT_BASE_URL))
    username = target_config.get("username", config.get("username", DEFAULT_USERNAME))
    password = target_config.get("password", config.get("password", DEFAULT_PASSWORD))
    
    logging.info(f"\n{'='*60}")
    logging.info(f"🔄 同步到目标: {target_name} ({base_url})")
    logging.info(f"{'='*60}")
    
    try:
        # 创建客户端
        client = Sport8Client(base_url, username, password)
        client.login()
        
        # 更新 args 中的配置
        original_base_url = args.base_url
        args.base_url = base_url
        
        # 同步订单
        if not args.bookings_only:
            logging.info(f"\n📦 同步订单到 {target_name}...")
            order_stats = sync_orders(args, client, state)
            logging.info(
                f"✅ {target_name} 订单同步完成: created={order_stats.created_orders}, "
                f"payments={order_stats.created_payments}, skipped={order_stats.skipped}"
            )
        
        # 同步锁定预订
        if not args.orders_only:
            logging.info(f"\n🔒 同步锁定预订到 {target_name}...")
            locked_stats = sync_locked_bookings(args, client, state)
            logging.info(
                f"✅ {target_name} 锁定预订同步完成: created={locked_stats.created_bookings}, "
                f"skipped={locked_stats.skipped}"
            )
        
        # 恢复原始配置
        args.base_url = original_base_url
        
        return True
        
    except Exception as e:
        logging.error(f"❌ 同步到 {target_name} 失败: {e}")
        return False


def main():
    """主函数 - 双地址同步"""
    print("=" * 70)
    print("🏟️ Sport8 双地址同步工具")
    print("=" * 70)
    print("\n目标地址:")
    print("  1. bakewell.cloud (主)")
    print("  2. 124.223.13.170 (备)")
    print()
    
    # 解析参数
    parser = argparse.ArgumentParser(description="Sync Sport8 to multiple targets")
    parser.add_argument("--config", default="config/sport8_sync_dual.json", 
                       help="Path to JSON config file")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--bookings-only", action="store_true", help="Only sync bookings")
    parser.add_argument("--orders-only", action="store_true", help="Only sync orders")
    
    args = parser.parse_args()
    
    # 加载配置
    config_path = Path(args.config).expanduser()
    config = load_config_file(config_path)
    
    if not config:
        logging.error(f"无法加载配置文件: {config_path}")
        sys.exit(1)
    
    # 设置日志
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"dual_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    
    logging.info("🚀 开始双地址同步")
    
    # 获取目标列表
    targets = config.get("targets", [])
    if not targets:
        # 如果没有 targets，使用主配置作为单个目标
        targets = [{
            "name": "primary",
            "base_url": config.get("base_url", DEFAULT_BASE_URL),
            "username": config.get("username", DEFAULT_USERNAME),
            "password": config.get("password", DEFAULT_PASSWORD)
        }]
    
    # 加载状态
    global state
    state = load_state()
    
    # 同步到每个目标
    results = {}
    for target in targets:
        success = sync_to_target(args, config, target)
        results[target.get("name", "unknown")] = success
    
    # 保存状态
    state["last_run"] = datetime.utcnow().isoformat()
    save_state(state)
    
    # 汇总结果
    print("\n" + "=" * 70)
    print("📊 同步结果汇总")
    print("=" * 70)
    for name, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"  {name}: {status}")
    
    all_success = all(results.values())
    if all_success:
        print("\n✅ 所有目标同步完成")
    else:
        print("\n⚠️  部分目标同步失败")
    
    print(f"\n日志文件: {log_file}")
    
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
