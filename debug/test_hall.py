#!/usr/bin/env python3
import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main.tools.module_converter import ModuleConverter

converter = ModuleConverter()

# 测试hall中的一个文件
file_path = r"C:\Workflow\xsh5\build\web-mobile\assets\hall\script\AgentBuy.js"

print(f"测试文件: {file_path}")
results = converter.process_module_file(file_path)

if results:
    print(f"找到 {len(results)} 个类定义")
    for result in results:
        class_info = result['class_info']
        print(f"类名: {class_info.get('name')}")
        print(f"继承自: {class_info.get('extends')}")
        print(f"装饰器: {class_info.get('decorators', [])}")
        print(f"属性: {len(class_info.get('properties', {}))}")
        print(f"方法: {len(class_info.get('methods', {}))}")
        
        # 保存测试文件
        output_dir = r"C:\Workflow\xsh5\build\web-mobile\assets\hall\script\typescript"
        converter.save_typescript_file(
            class_info, 
            result['ts_code'], 
            output_dir,
            "AgentBuy.js"
        )
else:
    print("未找到类定义")