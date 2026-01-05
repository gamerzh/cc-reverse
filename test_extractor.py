#!/usr/bin/env python3
"""
测试bundle_extractor在main bundle上的表现
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bundle_extractor

def test_main_bundle():
    bundle_path = r"C:\Workflow\xsh5\build\web-mobile\assets\main\index.81ec1.js"
    
    if not os.path.exists(bundle_path):
        print(f"文件不存在: {bundle_path}")
        return
    
    print(f"测试bundle: {bundle_path}")
    print(f"文件大小: {os.path.getsize(bundle_path)} 字节")
    
    # 读取文件
    with open(bundle_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 测试find_module_object
    print("\n=== 测试 find_module_object ===")
    result = bundle_extractor.find_module_object(content)
    if result:
        start, end = result
        print(f"找到模块对象: 位置 {start} - {end}")
        print(f"对象大小: {end - start} 字节")
        
        # 查看对象开头
        obj_start = max(0, start - 100)
        obj_end = min(len(content), start + 500)
        print(f"\n对象上下文:")
        print(content[obj_start:obj_end])
    else:
        print("未找到模块对象")
        
        # 尝试查找替代模式
        print("\n查找替代模式...")
        # 查找可能的模块对象模式: { ... }
        import re
        # 查找 { 后面跟着数字键
        pattern = r'\{\s*"\d+"\s*:'
        matches = list(re.finditer(pattern, content[:5000]))
        print(f"找到 {len(matches)} 个可能的对象开始")
        for i, match in enumerate(matches[:5]):
            print(f"  匹配 {i}: 位置 {match.start()}")
    
    # 测试extract_bundle
    print("\n=== 测试 extract_bundle ===")
    saved_count, output_dir = bundle_extractor.extract_bundle(bundle_path, None)
    print(f"保存的模块数: {saved_count}")
    print(f"输出目录: {output_dir}")
    
    if output_dir and os.path.exists(output_dir):
        print(f"输出目录内容:")
        for item in os.listdir(output_dir):
            print(f"  {item}")
    else:
        print("输出目录不存在")

if __name__ == "__main__":
    test_main_bundle()