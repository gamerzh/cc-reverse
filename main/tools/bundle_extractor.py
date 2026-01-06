#!/usr/bin/env python3
"""
bundle_extractor.py - Webpack bundle文件提取器
"""

import os
import re
import json


def extract_bundle(bundle_path, output_dir):
    """
    从bundle文件中提取模块
    
    Args:
        bundle_path: bundle文件路径
        output_dir: 输出目录
    
    Returns:
        tuple: (saved_count, output_dir)
    """
    saved_count = 0
    
    try:
        # 读取bundle文件内容
        with open(bundle_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 查找Webpack模块定义
        # 简化版本：查找所有cc._RF.push调用
        rf_push_pattern = r'cc\._RF\.push\([^,]+,\s*"([^"]+)",\s*"([^"]+)"\)\s*\(\s*function\s*\([^)]*\)\s*\{([\s\S]*?)\}\)'
        matches = re.finditer(rf_push_pattern, content)
        
        for match in matches:
            module_name = match.group(1)
            file_path = match.group(2)
            module_code = match.group(3)
            
            # 生成模块文件
            module_file_path = os.path.join(output_dir, f"{module_name}.js")
            
            # 添加模块包装
            full_code = f"// 模块: {module_name}\n" \
                      f"// 原始路径: {file_path}\n" \
                      f"\n" \
                      f"(function() {{\n" \
                      f"{module_code}\n" \
                      f"}})();\n"
            
            # 写入文件
            with open(module_file_path, 'w', encoding='utf-8') as f:
                f.write(full_code)
            
            saved_count += 1
        
        # 查找其他可能的模块定义模式
        if saved_count == 0:
            # 尝试查找模块对象定义
            module_obj_pattern = r'(\w+)\s*=\s*\{\s*(\w+:\s*function\s*\([^)]*\)\s*\{[^}]*\},\s*)*\w+:\s*function\s*\([^)]*\)\s*\{[^}]*\}\s*\}'
            matches = re.finditer(module_obj_pattern, content)
            
            for i, match in enumerate(matches):
                module_name = f"module_{i}"
                module_code = match.group(0)
                
                module_file_path = os.path.join(output_dir, f"{module_name}.js")
                with open(module_file_path, 'w', encoding='utf-8') as f:
                    f.write(module_code)
                
                saved_count += 1
    
    except Exception as e:
        print(f"提取bundle失败: {e}")
    
    return saved_count, output_dir
