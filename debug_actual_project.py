#!/usr/bin/env python3
"""
调试实际项目处理流程的脚本
"""

import os
import sys
import shutil
import json

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 导入核心模块
from src.core.codeAnalyzer import codeAnalyzer
from src.core.reverseEngine import reverseProject, logger as engine_logger

# 设置详细日志
engine_logger().set_level('debug')
engine_logger().set_verbose(True)

print("=" * 60)
print("调试实际项目处理流程")
print("=" * 60)

# 你实际的项目路径
actual_project_path = r'C:\Workflow\xsh5\build\web-mobile'
# 输出路径
output_path = os.path.join(os.path.dirname(__file__), 'debug_output')

print(f"项目路径: {actual_project_path}")
print(f"输出路径: {output_path}")

# 检查项目路径是否存在
if not os.path.exists(actual_project_path):
    print(f"错误: 项目路径不存在: {actual_project_path}")
    sys.exit(1)

# 检查项目结构
print("\n项目文件结构:")
for item in os.listdir(actual_project_path):
    item_path = os.path.join(actual_project_path, item)
    if os.path.isfile(item_path):
        print(f"  [文件] {item}")
    else:
        print(f"  [目录] {item}")

# 检查是否有settings.js或main.js等关键文件
key_files = ['settings.js', 'main.js', 'project.js', 'src/settings.js', 'src/project.js']
found_key_files = []
for key_file in key_files:
    full_path = os.path.join(actual_project_path, key_file)
    if os.path.exists(full_path):
        found_key_files.append(key_file)
        size = os.path.getsize(full_path)
        print(f"  ✓ 找到关键文件: {key_file} ({size} 字节)")

if not found_key_files:
    print("  ✗ 未找到关键文件，可能不支持此项目结构")
    sys.exit(1)

# 检查settings.js内容
for key_file in found_key_files:
    if 'settings' in key_file:
        full_path = os.path.join(actual_project_path, key_file)
        print(f"\n{key_file} 内容预览:")
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content[:500] + '...')
        break

# 运行逆向工程
try:
    print("\n" + "=" * 60)
    print("开始处理项目...")
    print("=" * 60)
    
    # 清理之前的输出
    if os.path.exists(output_path):
        shutil.rmtree(output_path)
    
    # 调用逆向工程
    success = reverseProject({
        "sourcePath": actual_project_path,
        "outputPath": output_path,
        "verbose": True,
        "silent": False,
        "versionHint": "2.4.x"  # 尝试指定版本
    })
    
    if success:
        print("\n" + "=" * 60)
        print("处理完成！检查输出结果:")
        print("=" * 60)
        
        # 检查输出目录
        if os.path.exists(output_path):
            print(f"输出目录: {output_path}")
            
            # 检查assets/scripts目录
            scripts_dir = os.path.join(output_path, 'assets', 'scripts')
            if os.path.exists(scripts_dir):
                scripts = [f for f in os.listdir(scripts_dir) if f.endswith('.js')]
                print(f"脚本目录: {scripts_dir}")
                print(f"生成的脚本数量: {len(scripts)}")
                if scripts:
                    print(f"脚本列表: {scripts}")
                else:
                    print("✗ 未生成任何脚本文件！")
                    
                    # 检查是否检测到组件
                    print("\n检查组件检测情况:")
                    print(f"检测到的组件数量: {len(codeAnalyzer.analyzed_data.get('components', []))}")
                    if not codeAnalyzer.analyzed_data.get('components', []):
                        print("✗ 未检测到任何组件！")
                        
                        # 尝试手动分析settings.js
                        print("\n尝试手动分析settings.js:")
                        for key_file in found_key_files:
                            if 'settings' in key_file:
                                full_path = os.path.join(actual_project_path, key_file)
                                with open(full_path, 'r', encoding='utf-8') as f:
                                    settings_content = f.read()
                                
                                # 尝试提取jsList
                                try:
                                    # 尝试直接解析CCSettings
                                    if 'window._CCSettings' in settings_content:
                                        # 提取CCSettings内容
                                        settings_part = settings_content.split('window._CCSettings = ')[1]
                                        settings_part = settings_part.split(';')[0]
                                        cc_settings = json.loads(settings_part)
                                        js_list = cc_settings.get('jsList', [])
                                        print(f"从settings中提取到 {len(js_list)} 个脚本文件")
                                        if js_list:
                                            print(f"前5个脚本: {js_list[:5]}")
                                except Exception as e:
                                    print(f"解析CCSettings失败: {e}")
                                    
                                # 尝试用正则表达式提取
                                import re
                                js_list_match = re.search(r'jsList\s*:\s*\[(.*?)\]', settings_content, re.DOTALL)
                                if js_list_match:
                                    js_list_str = js_list_match.group(1)
                                    # 简单解析数组
                                    js_files = [item.strip().strip('"\'') for item in js_list_str.split(',') if item.strip()]
                                    print(f"用正则提取到 {len(js_files)} 个脚本文件")
                                    if js_files:
                                        print(f"前5个脚本: {js_files[:5]}")
                                    
                                    # 尝试分析第一个脚本文件
                                    if js_files:
                                        first_js = js_files[0]
                                        js_full_path = os.path.join(actual_project_path, first_js)
                                        if os.path.exists(js_full_path):
                                            print(f"\n尝试分析第一个脚本: {first_js}")
                                            with open(js_full_path, 'r', encoding='utf-8') as f:
                                                js_content = f.read()
                                            
                                            # 重置代码分析器
                                            codeAnalyzer.analyzed_data = {
                                                "scripts": [],
                                                "resources": [],
                                                "components": [],
                                                "nodes": [],
                                                "dependencies": {}
                                            }
                                            
                                            # 分析该脚本
                                            codeAnalyzer.analyze(js_content, first_js)
                                            
                                            # 检查结果
                                            print(f"分析结果: 检测到 {len(codeAnalyzer.analyzed_data.get('components', []))} 个组件")
                                            if codeAnalyzer.analyzed_data.get('components', []):
                                                print(f"检测到的组件: {[c['name'] for c in codeAnalyzer.analyzed_data.get('components', [])]}")
                                            else:
                                                print("✗ 仍然未检测到组件！")
                                                # 检查脚本中是否包含cc.Class
                                                import re
                                                class_count = len(re.findall(r'cc\.Class', js_content))
                                                print(f"脚本中包含 {class_count} 个 cc.Class 调用")
                                                
                                                # 显示部分内容
                                                print("\n脚本内容预览 (前1000字符):")
                                                print(js_content[:1000] + '...')
                                break
            else:
                print("✗ 脚本目录不存在！")
        else:
            print("✗ 输出目录不存在！")
    else:
        print("\n✗ 处理失败！")
        
except Exception as e:
    print(f"\n处理过程中发生异常: {e}")
    import traceback
    traceback.print_exc()
    
print("\n" + "=" * 60)
print("调试结束")
print("=" * 60)
