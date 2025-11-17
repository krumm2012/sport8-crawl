#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用验证码识别工具
支持多种识别方法，适用于 https://stadium.sports8.com.cn/StadiumHelper/
"""

import os
import sys
from pathlib import Path
from PIL import Image
import io

class CaptchaRecognizer:
    """验证码识别器"""
    
    def __init__(self):
        self.method = "ddddocr"  # 默认使用 ddddocr
        self.ocr = None
        self._init_ocr()
    
    def _init_ocr(self):
        """初始化 OCR 引擎"""
        try:
            import ddddocr
            self.ocr = ddddocr.DdddOcr(show_ad=False)
            print("✓ 已加载 ddddocr 识别引擎")
        except ImportError:
            print("⚠️  未安装 ddddocr，请运行: pip install ddddocr")
            self.ocr = None
    
    def recognize_from_file(self, image_path):
        """
        从文件识别验证码
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            str: 识别结果，失败返回 None
        """
        if not os.path.exists(image_path):
            print(f"❌ 文件不存在: {image_path}")
            return None
        
        try:
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            return self.recognize_from_bytes(image_bytes)
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return None
    
    def recognize_from_bytes(self, image_bytes):
        """
        从字节数据识别验证码
        
        Args:
            image_bytes: 图片字节数据
            
        Returns:
            str: 识别结果，失败返回 None
        """
        if not self.ocr:
            print("❌ OCR 引擎未初始化")
            return None
        
        try:
            # 使用 ddddocr 识别
            result = self.ocr.classification(image_bytes)
            
            # 清理结果（去除空格、转大写）
            result = result.strip().upper()
            
            # 过滤非字母数字字符
            result = ''.join(c for c in result if c.isalnum())
            
            return result
        except Exception as e:
            print(f"❌ 识别失败: {e}")
            return None
    
    def recognize_from_url(self, session, captcha_url):
        """
        从 URL 识别验证码
        
        Args:
            session: requests.Session 对象
            captcha_url: 验证码 URL
            
        Returns:
            str: 识别结果，失败返回 None
        """
        try:
            resp = session.get(captcha_url, timeout=10)
            resp.raise_for_status()
            return self.recognize_from_bytes(resp.content)
        except Exception as e:
            print(f"❌ 获取验证码失败: {e}")
            return None
    
    def preprocess_image(self, image_bytes, save_path=None):
        """
        预处理图片（可选）
        
        Args:
            image_bytes: 原始图片字节
            save_path: 保存路径（可选）
            
        Returns:
            bytes: 处理后的图片字节
        """
        try:
            from PIL import Image, ImageEnhance, ImageFilter
            
            # 打开图片
            img = Image.open(io.BytesIO(image_bytes))
            
            # 转换为 RGB
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 增强对比度
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)
            
            # 锐化
            img = img.filter(ImageFilter.SHARPEN)
            
            # 保存（如果需要）
            if save_path:
                img.save(save_path)
                print(f"✓ 预处理后的图片已保存: {save_path}")
            
            # 转换回字节
            output = io.BytesIO()
            img.save(output, format='PNG')
            return output.getvalue()
        except Exception as e:
            print(f"⚠️  预处理失败: {e}，使用原图")
            return image_bytes
    
    def batch_test(self, image_dir):
        """
        批量测试目录中的验证码图片
        
        Args:
            image_dir: 图片目录
        """
        image_dir = Path(image_dir)
        if not image_dir.exists():
            print(f"❌ 目录不存在: {image_dir}")
            return
        
        print(f"\n{'='*70}")
        print(f"批量测试验证码识别")
        print(f"目录: {image_dir}")
        print(f"{'='*70}\n")
        
        # 查找所有图片
        image_files = list(image_dir.glob("*.png")) + list(image_dir.glob("*.jpg"))
        
        if not image_files:
            print("❌ 未找到图片文件")
            return
        
        print(f"找到 {len(image_files)} 个图片文件\n")
        
        success_count = 0
        results = []
        
        for i, img_path in enumerate(image_files, 1):
            print(f"[{i}/{len(image_files)}] {img_path.name}")
            
            result = self.recognize_from_file(img_path)
            
            if result:
                print(f"  ✓ 识别结果: {result}")
                success_count += 1
                results.append((img_path.name, result))
            else:
                print(f"  ✗ 识别失败")
                results.append((img_path.name, "失败"))
            
            print()
        
        # 统计
        print(f"{'='*70}")
        print(f"识别完成: {success_count}/{len(image_files)} 成功")
        print(f"成功率: {success_count/len(image_files)*100:.1f}%")
        print(f"{'='*70}\n")
        
        # 显示所有结果
        print("所有结果:")
        for filename, result in results:
            print(f"  {filename}: {result}")


def test_single_image(image_path):
    """测试单个图片"""
    print(f"\n{'='*70}")
    print(f"测试单个验证码")
    print(f"{'='*70}\n")
    
    recognizer = CaptchaRecognizer()
    
    print(f"图片: {image_path}")
    result = recognizer.recognize_from_file(image_path)
    
    if result:
        print(f"\n✓ 识别结果: {result}")
        print(f"  长度: {len(result)} 个字符")
    else:
        print(f"\n✗ 识别失败")
    
    print(f"\n{'='*70}")


def test_with_preprocessing(image_path):
    """测试预处理后的识别效果"""
    print(f"\n{'='*70}")
    print(f"测试预处理 + 识别")
    print(f"{'='*70}\n")
    
    recognizer = CaptchaRecognizer()
    
    # 读取原图
    with open(image_path, 'rb') as f:
        original_bytes = f.read()
    
    # 原图识别
    print("1. 原图识别:")
    result1 = recognizer.recognize_from_bytes(original_bytes)
    print(f"   结果: {result1 or '失败'}")
    
    # 预处理后识别
    print("\n2. 预处理后识别:")
    processed_bytes = recognizer.preprocess_image(
        original_bytes,
        save_path="captcha_preprocessed.png"
    )
    result2 = recognizer.recognize_from_bytes(processed_bytes)
    print(f"   结果: {result2 or '失败'}")
    
    print(f"\n{'='*70}")


def interactive_test():
    """交互式测试"""
    print(f"\n{'='*70}")
    print(f"交互式验证码识别测试")
    print(f"{'='*70}\n")
    
    recognizer = CaptchaRecognizer()
    
    while True:
        print("\n选项:")
        print("  1. 测试单个图片")
        print("  2. 批量测试目录")
        print("  3. 测试预处理效果")
        print("  0. 退出")
        
        choice = input("\n请选择 (0-3): ").strip()
        
        if choice == "0":
            print("再见！")
            break
        elif choice == "1":
            path = input("请输入图片路径: ").strip()
            test_single_image(path)
        elif choice == "2":
            path = input("请输入目录路径: ").strip()
            recognizer.batch_test(path)
        elif choice == "3":
            path = input("请输入图片路径: ").strip()
            test_with_preprocessing(path)
        else:
            print("❌ 无效选项")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="验证码识别工具")
    parser.add_argument("--file", "-f", help="单个图片文件路径")
    parser.add_argument("--dir", "-d", help="批量测试目录")
    parser.add_argument("--preprocess", "-p", action="store_true", help="测试预处理效果")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互式模式")
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_test()
    elif args.file:
        if args.preprocess:
            test_with_preprocessing(args.file)
        else:
            test_single_image(args.file)
    elif args.dir:
        recognizer = CaptchaRecognizer()
        recognizer.batch_test(args.dir)
    else:
        # 默认：测试 data/captcha 目录
        default_dir = Path(__file__).parent / "data" / "captcha"
        if default_dir.exists():
            print("使用默认目录: data/captcha/")
            recognizer = CaptchaRecognizer()
            recognizer.batch_test(default_dir)
        else:
            print("使用方法:")
            print("  python3 captcha_recognizer.py -f <图片路径>")
            print("  python3 captcha_recognizer.py -d <目录路径>")
            print("  python3 captcha_recognizer.py -i  # 交互式")
            print("  python3 captcha_recognizer.py     # 测试默认目录")


