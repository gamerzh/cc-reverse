#!/usr/bin/env python3
"""
测试版：专门处理带MD5值的settings文件
"""

import os
import sys
import glob
import re
import json

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 导入核心模块
from src.core.codeAnalyzer import codeAnalyzer
from src.utils.logger import logger

# 设置详细日志
logger().set_level('debug')
logger().set_verbose(True)

def detect_and_process(project_path, output_path):
    """
    直接检测和处理项目，专门处理带MD5值的文件
    """
    print(f"处理项目: {project_path}")
    print(f"输出路径: {output_path}")
    
    # 1. 查找settings文件，支持带MD5值
    print("\n1. 查找settings文件:")
    settings_patterns = [
        os.path.join(project_path, 'src', 'settings*.js'),
        os.path.join(project_path, 'settings*.js'),
        os.path.join(project_path, 'src', 'main*.js'),
        os.path.join(project_path, 'main*.js')
    ]
    
    settings_file = None
    for pattern in settings_patterns:
        matches = glob.glob(pattern)
        if matches:
            settings_file = matches[0]
            print(f"   ✓ 找到settings文件: {settings_file}")
            break
    
    if not settings_file:
        print("   ✗ 未找到settings文件！")
        return False
    
    # 2. 查找资源目录
    print("\n2. 查找资源目录:")
    res_paths = [
        os.path.join(project_path, 'assets'),
        os.path.join(project_path, 'res'),
        os.path.join(project_path, 'src', 'assets'),
        os.path.join(project_path, 'src', 'res')
    ]
    
    res_dir = None
    for path in res_paths:
        if os.path.exists(path):
            res_dir = path
            print(f"   ✓ 找到资源目录: {res_dir}")
            break
    
    if not res_dir:
        print("   ✗ 未找到资源目录！")
        return False
    
    # 3. 查找project文件或使用settings文件
    print("\n3. 查找project文件:")
    project_patterns = [
        os.path.join(project_path, 'src', 'project*.js'),
        os.path.join(project_path, 'project*.js'),
        os.path.join(project_path, 'src', 'main*.js'),
        os.path.join(project_path, 'main*.js')
    ]
    
    project_file = None
    for pattern in project_patterns:
        matches = glob.glob(pattern)
        if matches:
            project_file = matches[0]
            print(f"   ✓ 找到project文件: {project_file}")
            break
    
    if not project_file:
        project_file = settings_file
        print(f"   ✗ 未找到project文件，使用settings文件代替: {project_file}")
    
    # 4. 读取settings文件，提取jsList
    print("\n4. 分析settings文件:")
    with open(settings_file, 'r', encoding='utf-8') as f:
        settings_content = f.read()
    
    print(f"   读取文件完成，大小: {len(settings_content)} 字符")
    
    # 提取CCSettings
    cc_settings = None
    js_list = []
    
    # 尝试多种方式提取CCSettings
    patterns_to_try = [
        # window._CCSettings = {...}
        r'window\._CCSettings\s*=\s*(\{[\s\S]*?\});',
        # _CCSettings = {...}
        r'_CCSettings\s*=\s*(\{[\s\S]*?\});',
        # CCSettings = {...}
        r'CCSettings\s*=\s*(\{[\s\S]*?\});',
        # var _CCSettings = {...}
        r'var\s+_CCSettings\s*=\s*(\{[\s\S]*?\});',
        # const _CCSettings = {...}
        r'const\s+_CCSettings\s*=\s*(\{[\s\S]*?\});',
        # let _CCSettings = {...}
        r'let\s+_CCSettings\s*=\s*(\{[\s\S]*?\});'
    ]
    
    for pattern in patterns_to_try:
        match = re.search(pattern, settings_content)
        if match:
            print(f"   ✓ 使用模式 '{pattern[:30]}...' 找到CCSettings")
            settings_str = match.group(1)
            try:
                cc_settings = json.loads(settings_str)
                js_list = cc_settings.get('jsList', [])
                print(f"   ✓ 提取到jsList，包含 {len(js_list)} 个文件")
                if js_list[:3]:
                    print(f"   ✓ 前3个文件: {js_list[:3]}")
                break
            except Exception as e:
                print(f"   ✗ 解析CCSettings失败: {e}")
                continue
    
    if not cc_settings:
        print("   ✗ 无法提取CCSettings！尝试直接查找jsList")
        # 尝试直接查找jsList
        js_list_match = re.search(r'jsList\s*:\s*\[(.*?)\]', settings_content, re.DOTALL)
        if js_list_match:
            js_list_str = js_list_match.group(1)
            js_list = [item.strip().strip('"') for item in js_list_str.split(',') if item.strip()]
            print(f"   ✓ 直接提取到jsList: {len(js_list)} 个文件")
    
    # 5. 读取并分析所有脚本文件
    print("\n5. 分析脚本文件:")
    all_scripts = []
    
    # 先分析settings文件
    print(f"   分析settings文件: {settings_file}")
    codeAnalyzer.analyze(settings_content, settings_file)
    
    # 分析jsList中的文件
    if js_list:
        print(f"   分析jsList中的 {len(js_list)} 个文件:")
        for js_file in js_list:
            full_path = os.path.join(project_path, js_file)
            if not os.path.exists(full_path):
                # 尝试在src目录下查找
                full_path = os.path.join(project_path, 'src', js_file)
            
            if os.path.exists(full_path):
                print(f"      ✓ 分析文件: {full_path}")
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                codeAnalyzer.analyze(content, full_path)
                all_scripts.append(full_path)
            else:
                print(f"      ✗ 未找到文件: {js_file}")
    
    # 6. 分析project文件
    print(f"\n6. 分析project文件: {project_file}")
    with open(project_file, 'r', encoding='utf-8') as f:
        project_content = f.read()
    codeAnalyzer.analyze(project_content, project_file)
    
    # 7. 显示分析结果
    print("\n7. 分析结果:")
    components = codeAnalyzer.analyzed_data.get('components', [])
    print(f"   检测到 {len(components)} 个组件")
    if components:
        print(f"   组件列表: {[c['name'] for c in components]}")
        
        # 8. 生成脚本文件
        print("\n8. 生成脚本文件:")
        scripts_dir = os.path.join(output_path, 'assets', 'scripts')
        os.makedirs(scripts_dir, exist_ok=True)
        
        for component in components:
            script_name = component['name'] + '.js'
            script_path = os.path.join(scripts_dir, script_name)
            # 生成脚本内容
            content = f"cc.Class({{\n"
            content += f"    name: '{component['name']}',\n"
            content += f"    extends: {component['extends']},\n"
            content += f"    properties: {json.dumps(component.get('properties', {}), indent=4)},\n"
            content += f"    onLoad: function() {{\n        // onLoad\n    }},\n"
            content += f"    start: function() {{\n        // start\n    }}\n"
            content += f"}});\n"
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"      ✓ 生成脚本: {script_path}")
    else:
        print("   ✗ 未检测到任何组件！")
        # 检查脚本中是否有cc.Class
        cc_class_count = settings_content.count('cc.Class(') + project_content.count('cc.Class(')
        print(f"   脚本中包含 {cc_class_count} 个cc.Class调用")

if __name__ == '__main__':
    # 你的项目路径
    project_path = r'C:\Workflow\xsh5\build\web-mobile'
    # 输出路径
    output_path = os.path.join(os.path.dirname(__file__), 'md5_fix_output')
    
    # 调用处理函数
    detect_and_process(project_path, output_path)