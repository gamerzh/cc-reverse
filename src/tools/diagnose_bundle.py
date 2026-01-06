#!/usr/bin/env python3
"""
诊断bundle文件
"""

import os
import sys
import re

def diagnose_bundle(bundle_path):
    print(f"诊断文件: {bundle_path}")
    print(f"文件大小: {os.path.getsize(bundle_path) if os.path.exists(bundle_path) else '不存在'} 字节")
    
    if not os.path.exists(bundle_path):
        print("文件不存在")
        return
    
    # 读取前5000个字符
    with open(bundle_path, 'r', encoding='utf-8') as f:
        content = f.read(5000)
    
    print("\n文件开头:")
    print(content[:500])
    
    # 检查Webpack特征
    webpack_patterns = [
        r'window\.__require\s*=\s*function',
        r'function\(e,t,o\)',
        r'cc\._RF\.push',
        r'this&&this\.__extends',
        r'this&&this\.__decorate',
        r'Object\.defineProperty\(o,"__esModule"',
    ]
    
    print("\nWebpack特征检测:")
    for pattern in webpack_patterns:
        if re.search(pattern, content, re.MULTILINE | re.DOTALL):
            print(f"  ✓ {pattern}")
        else:
            print(f"  ✗ {pattern}")
    
    # 检查是否包含模块对象
    if 'window.__require=function' in content:
        print("\n找到 window.__require=function 模式")
        # 尝试查找模块对象
        start_idx = content.find('window.__require=function')
        if start_idx != -1:
            print(f"  位置: {start_idx}")
    else:
        print("\n未找到 window.__require=function 模式")
    
    # 检查文件扩展名和目录
    print(f"\n文件目录: {os.path.dirname(bundle_path)}")
    print(f"文件名: {os.path.basename(bundle_path)}")

if __name__ == "__main__":
 # 测试main和internal bundle
    base_dir = r"C:\Workflow\xsh5\build\web-mobile\assets"
    
    for bundle_name in ['main', 'internal']:
        bundle_dir = os.path.join(base_dir, bundle_name)
        if os.path.exists(bundle_dir):
            # 查找index.*.js文件
            import glob
            pattern = os.path.join(bundle_dir, 'index.*.js')
            matches = glob.glob(pattern)
            if matches:
                bundle_path = matches[0]
                diagnose_bundle(bundle_path)
                print("\n" + "="*80 + "\n")
            else:
                print(f"未找到 {bundle_name} bundle文件")
        else:
            print(f"目录不存在: {bundle_dir}")