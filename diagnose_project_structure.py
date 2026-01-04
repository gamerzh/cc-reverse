#!/usr/bin/env python3
"""
诊断Cocos Creator项目结构的脚本
"""

import os
import sys
import re

print("=" * 60)
print("诊断Cocos Creator项目结构")
print("=" * 60)

# 你实际的项目路径
actual_project_path = r'C:\Workflow\xsh5\build\web-mobile'

print(f"项目路径: {actual_project_path}")

# 检查项目路径是否存在
if not os.path.exists(actual_project_path):
    print(f"错误: 项目路径不存在: {actual_project_path}")
    sys.exit(1)

print("\n1. 扫描项目根目录结构:")
root_items = os.listdir(actual_project_path)
for item in root_items:
    item_path = os.path.join(actual_project_path, item)
    if os.path.isfile(item_path):
        size = os.path.getsize(item_path)
        print(f"   [文件] {item} ({size} 字节)")
    else:
        print(f"   [目录] {item}")

# 查找所有可能的关键文件
print("\n2. 搜索可能的关键文件:")
key_file_patterns = [
    r'settings.*\.js',
    r'main.*\.js',
    r'project.*\.js',
    r'app.*\.js',
    r'game.*\.js',
    r'index.*\.js'
]

all_files = []
for root, dirs, files in os.walk(actual_project_path):
    for file in files:
        if file.endswith('.js'):
            all_files.append(os.path.join(root, file))

print(f"   找到 {len(all_files)} 个JavaScript文件")

# 搜索包含CCSettings或cc.Class的文件
print("\n3. 搜索包含Cocos Creator关键内容的文件:")
cocos_files = []
for file_path in all_files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否包含Cocos Creator相关内容
        if any(keyword in content for keyword in ['CCSettings', '_CCSettings', 'cc.Class', 'window.cc', 'cocos2d']):
            cocos_files.append(file_path)
            # 显示文件路径和关键内容
            rel_path = os.path.relpath(file_path, actual_project_path)
            # 计算文件大小
            size = os.path.getsize(file_path)
            # 检查包含的关键内容
            keywords_found = []
            if 'CCSettings' in content:
                keywords_found.append('CCSettings')
            if '_CCSettings' in content:
                keywords_found.append('_CCSettings')
            if 'cc.Class' in content:
                keywords_found.append('cc.Class')
            if 'window.cc' in content:
                keywords_found.append('window.cc')
            if 'cocos2d' in content:
                keywords_found.append('cocos2d')
            print(f"   ✓ {rel_path} ({size} 字节) - 包含: {', '.join(keywords_found)}")
    except Exception as e:
        print(f"   ✗ {os.path.relpath(file_path, actual_project_path)} - 读取错误: {e}")

# 详细分析找到的Cocos文件
if cocos_files:
    print("\n4. 详细分析关键文件:")
    for i, file_path in enumerate(cocos_files[:3], 1):  # 只分析前3个文件
        try:
            rel_path = os.path.relpath(file_path, actual_project_path)
            print(f"\n   {i}. 分析文件: {rel_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查文件大小
            size = os.path.getsize(file_path)
            print(f"      文件大小: {size} 字节")
            
            # 查找CCSettings定义
            settings_matches = [
                re.search(r'window\._CCSettings\s*=\s*\{', content),
                re.search(r'var\s+_CCSettings\s*=\s*\{', content),
                re.search(r'const\s+_CCSettings\s*=\s*\{', content),
                re.search(r'let\s+_CCSettings\s*=\s*\{', content),
                re.search(r'CCSettings\s*=\s*\{', content)
            ]
            
            settings_found = any(match for match in settings_matches)
            print(f"      包含CCSettings: {'是' if settings_found else '否'}")
            
            # 查找cc.Class定义
            class_count = len(re.findall(r'cc\.Class\s*\(', content))
            print(f"      包含cc.Class定义数量: {class_count}")
            
            # 查找jsList
            js_list_matches = re.findall(r'jsList\s*:\s*\[(.*?)\]', content, re.DOTALL)
            if js_list_matches:
                js_list_str = js_list_matches[0]
                # 简单解析数组
                js_files = [item.strip().strip('"\'') for item in js_list_str.split(',') if item.strip()]
                print(f"      包含jsList: {len(js_files)} 个文件")
                if js_files[:3]:
                    print(f"      前3个脚本: {js_files[:3]}")
            
            # 显示文件头部内容
            print(f"      文件头部预览 (前300字符):")
            print(f"      {content[:300]}{'...' if len(content) > 300 else ''}")
            
        except Exception as e:
            print(f"      分析错误: {e}")

# 检查是否有index.html文件
print("\n5. 检查HTML入口文件:")
html_files = []
for root, dirs, files in os.walk(actual_project_path):
    for file in files:
        if file.endswith('.html'):
            html_files.append(os.path.join(root, file))

if html_files:
    print(f"   找到 {len(html_files)} 个HTML文件:")
    for html_file in html_files:
        rel_path = os.path.relpath(html_file, actual_project_path)
        print(f"   ✓ {rel_path}")
        
        # 分析HTML文件，查找脚本引用
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找脚本引用
            script_matches = re.findall(r'<script[^>]*src=["\']([^"\']+)["\']', content)
            if script_matches:
                print(f"      引用 {len(script_matches)} 个脚本文件:")
                for script in script_matches[:5]:  # 只显示前5个
                    print(f"         - {script}")
        except Exception as e:
            print(f"      分析错误: {e}")
else:
    print("   未找到HTML文件")

# 总结和建议
print("\n6. 分析总结:")
if cocos_files:
    print(f"   ✓ 找到了 {len(cocos_files)} 个可能的Cocos Creator相关文件")
    print("   建议:")
    print("   1. 检查这些文件，确定哪个包含CCSettings定义")
    print("   2. 修改reverseEngine.py，添加对这些文件的支持")
    print("   3. 或者手动指定关键文件路径")
else:
    print("   ✗ 未找到明确的Cocos Creator相关文件")
    print("   可能的原因:")
    print("   1. 项目可能使用了不同版本的Cocos Creator")
    print("   2. 代码可能被高度压缩或加密")
    print("   3. 项目可能使用了非标准的构建配置")
    print("   建议:")
    print("   1. 检查项目是否有其他构建输出")
    print("   2. 查看原始Cocos Creator项目配置")
    print("   3. 尝试手动分析主要的JavaScript文件")

print("\n" + "=" * 60)
print("诊断结束")
print("=" * 60)
