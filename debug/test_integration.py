#!/usr/bin/env python3
"""
测试bundleProcessor集成
"""

import os
import sys

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.bundleProcessor import bundleProcessor

def test_bundle_processing():
    """测试bundle处理"""
    # 测试文件路径（假设存在）
    test_bundle = r"C:\Workflow\xsh5\build\web-mobile\assets\fhpoker\fhpoker.xxxx.js"
    
    if not os.path.exists(test_bundle):
        print(f"测试文件不存在: {test_bundle}")
        # 尝试查找其他bundle文件
        test_dir = r"C:\Workflow\xsh5\build\web-mobile\assets"
        for root, dirs, files in os.walk(test_dir):
            for file in files:
                if file.endswith('.js') and not file.startswith('index.'):
                    test_bundle = os.path.join(root, file)
                    print(f"尝试使用: {test_bundle}")
                    break
            if test_bundle and os.path.exists(test_bundle):
                break
    
    if not os.path.exists(test_bundle):
        print("未找到任何bundle文件，跳过测试")
        return
    
    print(f"测试bundle文件: {test_bundle}")
    
    # 检查是否为Webpack bundle
    is_bundle = bundleProcessor.is_webpack_bundle(test_bundle)
    print(f"是否为Webpack bundle: {is_bundle}")
    
    if is_bundle:
        # 提取模块
        print("提取模块...")
        extraction_result = bundleProcessor.extract_bundle_modules(test_bundle, None)
        
        if extraction_result:
            print(f"提取结果: {extraction_result}")
            
            # 转换为TypeScript
            print("转换为TypeScript...")
            conversion_result = bundleProcessor.convert_modules_to_typescript(extraction_result)
            
            if conversion_result:
                print(f"转换结果: {len(conversion_result)} 个类")
                for i, cls in enumerate(conversion_result[:3]):
                    print(f"  类 {i+1}: {cls.get('class_info', {}).get('name')}")
            else:
                print("转换失败")
        else:
            print("提取失败")
    else:
        print("不是Webpack bundle文件")

if __name__ == "__main__":
    test_bundle_processing()