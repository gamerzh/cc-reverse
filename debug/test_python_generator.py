#!/usr/bin/env python3
"""
调试脚本：仅测试Python生成器部分
"""

import os
import json
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# 导入生成器
from code_reverse.py_generator.gen_ts import TypeScriptGenerator

def create_test_json():
    """创建测试用的JSON数据，格式与js_analyzer生成的一致"""
    test_json = [
        {
            "module": "test123",
            "imports": {},
            "staticProperties": ["_config", "version"],
            "classDefinitions": [
                {
                    "type": "cc_class",
                    "name": "TestUI",
                    "extends": "cc.Component",
                    "properties": [
                        {
                            "name": "label",
                            "type": "cc.Label",
                            "defaultValue": "unknown"
                        },
                        {
                            "name": "score",
                            "type": "Number",
                            "defaultValue": 0
                        }
                    ],
                    "methods": [
                        {
                            "name": "onLoad",
                            "params": [],
                            "type": "function"
                        },
                        {
                            "name": "start",
                            "params": [],
                            "type": "function"
                        },
                        {
                            "name": "updateScore",
                            "params": [],
                            "type": "function"
                        }
                    ]
                }
            ]
        }
    ]
    
    # 保存到文件
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_path = os.path.join(output_dir, "analysis_result.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(test_json, f, indent=2, ensure_ascii=False)
    
    return output_path

def run_test():
    """运行测试"""
    print("开始测试Python生成器...")
    
    # 1. 创建测试JSON
    print("\n1. 创建测试JSON数据...")
    json_path = create_test_json()
    print(f"  创建的JSON文件: {json_path}")
    
    # 2. 运行Python生成器
    print("\n2. 运行Python生成器...")
    generator = TypeScriptGenerator()
    generator.generate_from_json(json_path, "output/generated_code", "typescript")
    
    # 3. 显示结果
    print("\n3. 显示生成的文件...")
    generated_files = []
    for root, dirs, files in os.walk("output/generated_code"):
        for file in files:
            generated_files.append(os.path.join(root, file))
    
    if generated_files:
        print(f"生成了 {len(generated_files)} 个文件：")
        for file in generated_files:
            print(f"  - {file}")
            
            # 显示文件内容前500字符
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"    内容（前500字符）:")
                print("    " + "="*40)
                print(content[:500] + ("..." if len(content) > 500 else ""))
                print("    " + "="*40)
    else:
        print("未生成任何文件！")
    
    print("\n测试完成！")

if __name__ == "__main__":
    run_test()
