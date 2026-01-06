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
from py_generator.gen_ts import TypeScriptGenerator

def create_test_json():
    """创建测试用的JSON数据"""
    test_json = {
        "generatedAt": "2026-01-06T03:38:08.509Z",
        "totalFiles": 1,
        "successful": 1,
        "failed": 0,
        "results": [
            {
                "success": True,
                "data": {
                    "filePath": "debug/test_sample.js",
                    "fileName": "test_sample.js",
                    "moduleName": "test123",
                    "dependencies": [],
                    "classDefinitions": [
                        {
                            "type": "cc_class",
                            "name": "TestUI",
                            "extends": "cc.Component",
                            "properties": [
                                {
                                    "name": "label",
                                    "type": "cc.Label",
                                    "defaultValue": None
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
                            ],
                            "statics": []
                        }
                    ],
                    "staticFields": [
                        {
                            "name": "_config",
                            "value": "unknown",
                            "type": "object"
                        }
                    ],
                    "methods": [],
                    "originalContent": "// 测试模块\ncc._RF.push(t, \"test123\", \"TestModule\");\n\ncc.Class({\n  name: \"TestUI\",\n  extends: cc.Component,\n  properties: {\n    label: { default: null, type: cc.Label },\n    score: { default: 0, type: Number }\n  },\n  onLoad: function() {\n    console.log(\"TestUI loaded\");\n  },\n  start: function() {\n    this.updateScore();\n  },\n  updateScore: function() {\n    if (this.label) {\n      this.label.string = \"Score: \" + this.score;\n    }\n  }\n});\n\n// 静态字段\ne._config = { host: \"localhost\", port: 8080 };\nObject.defineProperty(e, \"version\", {\n  get: function() { return \"1.0.0\"; }\n});\n\ncc._RF.pop();",
                    "prettifiedContent": "// 测试模块\ncc._RF.push(t, \"test123\", \"TestModule\");\n\ncc.Class({\n  name: \"TestUI\",\n  extends: cc.Component,\n  properties: {\n    label: { default: null, type: cc.Label },\n    score: { default: 0, type: Number }\n  },\n  onLoad: function() {\n    console.log(\"TestUI loaded\");\n  },\n  start: function() {\n    this.updateScore();\n  },\n  updateScore: function() {\n    if (this.label) {\n      this.label.string = \"Score: \" + this.score;\n    }\n  }\n});\n\n// 静态字段\ne._config = { host: \"localhost\", port: 8080 };\nObject.defineProperty(e, \"version\", {\n  get: function() { return \"1.0.0\"; }\n});\n\ncc._RF.pop();"
                }
            }
        ]
    }
    
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
