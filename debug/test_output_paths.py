#!/usr/bin/env python3
"""
测试输出路径计算
"""

import os
import sys

def test_path_calculation():
    """测试路径计算逻辑"""
    
    # 模拟用户输入
    source_path = r"C:\Workflow\xsh5\build\web-mobile"
    res_path = os.path.join(source_path, "assets")  # 假设资源目录是assets
    output_base_dir = r"C:\GitHub\cc-reverse\output"
    
    # 模拟bundle文件路径
    bundle_files = [
        os.path.join(res_path, "fhpoker", "index.xxxx.js"),
        os.path.join(res_path, "hall", "index.xxxx.js"),
        os.path.join(res_path, "main", "index.xxxx.js"),
    ]
    
    print("测试路径计算:")
    print(f"源项目路径: {source_path}")
    print(f"资源目录: {res_path}")
    print(f"输出基础目录: {output_base_dir}")
    print()
    
    for bundle_file in bundle_files:
        bundle_dir = os.path.dirname(bundle_file)
        bundle_name = os.path.basename(bundle_dir)
        
        # 计算相对路径（相对于资源目录）
        rel_path = os.path.relpath(bundle_dir, res_path)
        bundle_output_dir = os.path.join(output_base_dir, rel_path)
        
        print(f"Bundle: {bundle_file}")
        print(f"  Bundle目录: {bundle_dir}")
        print(f"  Bundle名称: {bundle_name}")
        print(f"  相对路径: {rel_path}")
        print(f"  输出目录: {bundle_output_dir}")
        
        # 测试bundle_extractor的逻辑
        print(f"  bundle_extractor输出检查:")
        print(f"    output_base_dir的basename: {os.path.basename(bundle_output_dir)}")
        print(f"    bundle_name: {bundle_name}")
        if os.path.basename(bundle_output_dir) == bundle_name:
            print(f"    -> 将创建: {os.path.join(bundle_output_dir, 'script')}")
        else:
            print(f"    -> 将创建: {os.path.join(bundle_output_dir, bundle_name, 'script')}")
        print()

if __name__ == "__main__":
    test_path_calculation()