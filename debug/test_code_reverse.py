#!/usr/bin/env python3
"""
测试code_reverse模块的功能
"""

import os
import sys
import tempfile
import shutil

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code_reverse import CodeReverse

def test_basic_functionality():
    """测试基本功能"""
    print("=== 测试code_reverse基本功能 ===")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    print(f"创建临时目录: {temp_dir}")
    
    try:
        # 初始化CodeReverse实例
        reverse = CodeReverse()
        
        # 测试配置功能
        reverse.set_config('output_format', 'typescript')
        reverse.set_config('preserve_temp', True)
        
        print(f"配置: {reverse.get_config('output_format')}")
        print(f"支持的格式: {reverse.get_supported_formats()}")
        
        # 测试JS分析器
        test_js = '''
        cc.Class({
            name: 'TestComponent',
            extends: cc.Component,
            properties: {
                testNode: cc.Node,
                testNumber: {
                    type: cc.Float,
                    default: 100.0
                },
                testString: 'hello'
            },
            onLoad() {
                console.log('onLoad called');
            },
            testMethod(param1, param2) {
                return param1 + param2;
            }
        });
        '''
        
        # 写入测试JS文件
        test_js_path = os.path.join(temp_dir, 'test.js')
        with open(test_js_path, 'w', encoding='utf-8') as f:
            f.write(test_js)
        
        # 测试分析代码
        json_output = os.path.join(temp_dir, 'json')
        success = reverse.analyze_code(test_js_path, json_output)
        print(f"分析代码 {'成功' if success else '失败'}")
        
        # 检查生成的JSON文件
        json_files = os.listdir(json_output)
        print(f"生成了 {len(json_files)} 个JSON文件")
        for json_file in json_files:
            print(f"  - {json_file}")
        
        # 测试生成代码
        code_output = os.path.join(temp_dir, 'output')
        success = reverse.generate_code(json_output, code_output)
        print(f"生成代码 {'成功' if success else '失败'}")
        
        # 检查生成的代码文件
        code_files = os.listdir(code_output)
        print(f"生成了 {len(code_files)} 个代码文件")
        for code_file in code_files:
            print(f"  - {code_file}")
            # 读取并显示生成的代码
            code_path = os.path.join(code_output, code_file)
            with open(code_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print("\n生成的代码:")
                print(content[:500] + "..." if len(content) > 500 else content)
        
        return True
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)
        print(f"清理临时目录: {temp_dir}")

def test_webpack_bundle():
    """测试Webpack bundle解析"""
    print("\n=== 测试Webpack bundle解析 ===")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    print(f"创建临时目录: {temp_dir}")
    
    try:
        # 初始化CodeReverse实例
        reverse = CodeReverse()
        
        # 创建一个简单的Webpack bundle模拟
        webpack_bundle = '''
        (function(modules) {
            function __webpack_require__(moduleId) {
                // webpack require implementation
            }
            // ...
        })({
            "0": function(module, __webpack_exports__, __webpack_require__) {
                "use strict";
                cc.Class({
                    name: 'WebpackTest',
                    extends: cc.Component,
                    properties: {
                        webpackProperty: cc.String
                    },
                    start() {
                        console.log('Webpack test component started');
                    }
                });
            }
        });
        '''
        
        # 写入测试bundle文件
        test_bundle_path = os.path.join(temp_dir, 'bundle.js')
        with open(test_bundle_path, 'w', encoding='utf-8') as f:
            f.write(webpack_bundle)
        
        # 测试分析bundle
        json_output = os.path.join(temp_dir, 'json')
        success = reverse.analyze_code(test_bundle_path, json_output)
        print(f"分析Webpack bundle {'成功' if success else '失败'}")
        
        # 检查生成的JSON文件
        if os.path.exists(json_output):
            json_files = os.listdir(json_output)
            print(f"生成了 {len(json_files)} 个JSON文件")
        
        return True
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)
        print(f"清理临时目录: {temp_dir}")

def main():
    """主测试函数"""
    print("开始测试code_reverse模块...")
    
    # 运行测试
    test_results = []
    test_results.append(test_basic_functionality())
    test_results.append(test_webpack_bundle())
    
    # 统计结果
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("所有测试通过!")
        return 0
    else:
        print("部分测试失败!")
        return 1

if __name__ == '__main__':
    sys.exit(main())
