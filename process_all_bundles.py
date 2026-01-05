#!/usr/bin/env python3
"""
批量处理所有bundle文件
"""

import os
import sys
import subprocess
from pathlib import Path

def find_bundle_files(base_dir):
    """查找所有bundle文件"""
    bundle_files = []
    
    # 使用glob查找所有index.*.js文件
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.startswith('index.') and file.endswith('.js'):
                bundle_path = os.path.join(root, file)
                bundle_files.append(bundle_path)
    
    return bundle_files

def extract_bundle(bundle_path):
    """提取bundle文件"""
    print(f"\n{'='*80}")
    print(f"提取bundle: {bundle_path}")
    print(f"{'='*80}")
    
    # 运行bundle_extractor.py
    cmd = [sys.executable, "bundle_extractor.py", bundle_path]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"提取成功!")
        
        # 从输出中提取提取的模块数
        for line in result.stdout.split('\n'):
            if '成功提取' in line or '成功保存' in line:
                print(f"  {line}")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"提取失败: {e}")
        print(f"标准错误: {e.stderr}")
        return False

def convert_modules(bundle_path):
    """转换提取的模块为TypeScript"""
    # 确定提取的模块目录
    bundle_dir = os.path.dirname(bundle_path)
    script_dir = os.path.join(bundle_dir, "script")
    
    if not os.path.exists(script_dir):
        print(f"脚本目录不存在: {script_dir}")
        return False
    
    # 统计.js文件数量
    js_files = [f for f in os.listdir(script_dir) if f.endswith('.js')]
    if not js_files:
        print(f"没有找到.js文件在 {script_dir}")
        return False
    
    print(f"找到 {len(js_files)} 个模块文件")
    
    # 创建TypeScript输出目录
    ts_dir = os.path.join(script_dir, "typescript")
    os.makedirs(ts_dir, exist_ok=True)
    
    # 导入并运行module_converter
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from module_converter import ModuleConverter
        
        converter = ModuleConverter()
        processed_count = 0
        
        # 处理每个.js文件（限制前10个以避免过多输出）
        for i, js_file in enumerate(js_files[:10]):
            file_path = os.path.join(script_dir, js_file)
            print(f"[{i+1}/{len(js_files[:10])}] 处理: {js_file}")
            
            results = converter.process_module_file(file_path)
            
            if results:
                for result in results:
                    # 保存TypeScript文件
                    converter.save_typescript_file(
                        result['class_info'], 
                        result['ts_code'], 
                        ts_dir,
                        js_file
                    )
                    processed_count += 1
            else:
                print(f"  -> 未提取到类信息")
        
        print(f"完成! 处理了 {processed_count} 个类到 {ts_dir}")
        return True
        
    except ImportError as e:
        print(f"导入module_converter失败: {e}")
        return False
    except Exception as e:
        print(f"转换过程中出错: {e}")
        return False

def main():
    """主函数"""
    base_dir = r"C:\Workflow\xsh5\build\web-mobile\assets"
    
    if not os.path.exists(base_dir):
        print(f"基础目录不存在: {base_dir}")
        return
    
    print(f"在 {base_dir} 中查找bundle文件...")
    
    # 查找bundle文件
    bundle_files = find_bundle_files(base_dir)
    
    if not bundle_files:
        print("未找到bundle文件")
        return
    
    print(f"找到 {len(bundle_files)} 个bundle文件:")
    for i, bundle in enumerate(bundle_files):
        print(f"  {i+1}. {bundle}")
    
    # 处理特定的bundle（hall, main, internal）
    target_bundles = ['hall', 'main', 'internal']
    
    for bundle_name in target_bundles:
        # 查找匹配的bundle文件
        matching_bundles = [b for b in bundle_files if f"\\{bundle_name}\\index." in b]
        
        if not matching_bundles:
            print(f"\n未找到 {bundle_name} bundle")
            continue
        
        bundle_path = matching_bundles[0]
        
        # 提取bundle
        if not extract_bundle(bundle_path):
            print(f"跳过 {bundle_name} 的转换")
            continue
        
        # 转换模块
        print(f"\n转换 {bundle_name} 的模块...")
        convert_modules(bundle_path)
    
    print(f"\n{'='*80}")
    print("批量处理完成!")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()