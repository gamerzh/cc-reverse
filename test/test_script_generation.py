#!/usr/bin/env python3
"""
测试脚本生成功能
"""

import os
import sys
import shutil

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 导入核心模块
from src.core.codeAnalyzer import codeAnalyzer
from src.core.projectGenerator import projectGenerator

# 重置代码分析器
codeAnalyzer.analyzed_data = {
    "scripts": [],
    "resources": [],
    "components": [],
    "nodes": [],
    "dependencies": {}
}

# 创建测试组件
test_components = [
    {
        "name": "HelloWorld",
        "extends": "cc.Component",
        "properties": {
            "label": {
                "default": None,
                "type": "cc.Label"
            }
        },
        "methods": {
            "onLoad": {"params": []},
            "start": {"params": []}
        }
    },
    {
        "name": "GameManager",
        "extends": "cc.Component",
        "properties": {
            "score": 0
        },
        "statics": {
            "instance": None
        }
    }
]

# 添加测试组件到分析数据
for component in test_components:
    codeAnalyzer.analyzed_data["components"].append(component)

# 创建测试输出目录
test_output = os.path.join(os.path.dirname(__file__), 'test_script_output')
if os.path.exists(test_output):
    shutil.rmtree(test_output)
os.makedirs(test_output, exist_ok=True)

print("=" * 60)
print("测试脚本生成功能")
print("=" * 60)

# 打印分析数据
print(f"组件数量: {len(codeAnalyzer.analyzed_data['components'])}")
print(f"组件列表: {[c['name'] for c in codeAnalyzer.analyzed_data['components']]}")

# 生成脚本
print("\n开始生成脚本...")
codeAnalyzer.generateScripts(test_output)

# 检查生成结果
scripts_dir = os.path.join(test_output, 'assets', 'scripts')
print(f"\n脚本目录: {scripts_dir}")
print(f"目录存在: {os.path.exists(scripts_dir)}")

if os.path.exists(scripts_dir):
    scripts = [f for f in os.listdir(scripts_dir) if f.endswith('.js')]
    print(f"生成的脚本数量: {len(scripts)}")
    print(f"脚本列表: {scripts}")
    
    # 打印脚本内容
    for script in scripts:
        script_path = os.path.join(scripts_dir, script)
        print(f"\n{script} 内容:")
        with open(script_path, 'r', encoding='utf-8') as f:
            print(f.read())

# 清理测试目录
shutil.rmtree(test_output)

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
