#!/usr/bin/env python3
"""
测试脚本 - 用于验证逆向引擎的当前状态
"""

import os
import sys
import shutil

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# 导入主函数
from main.main import cli

# 测试配置
test_source_path = "test_project"  # 替换为实际的测试项目路径
test_output_path = "test_output"

# 创建测试项目结构
def create_test_project():
    """创建测试项目结构"""
    print("创建测试项目结构...")
    
    # 创建基本目录结构
    os.makedirs(os.path.join(test_source_path, "src"), exist_ok=True)
    os.makedirs(os.path.join(test_source_path, "assets"), exist_ok=True)
    
    # 创建settings.js文件
    settings_content = """window._CCSettings = {
    jsList: [
        "assets/scripts/TestComponent.js"
    ],
    debugMode: 0
};
"""
    with open(os.path.join(test_source_path, "src", "settings.js"), "w") as f:
        f.write(settings_content)
    
    # 创建main.js文件
    main_content = """console.log("Cocos Creator project");
cc.game.run();
"""
    with open(os.path.join(test_source_path, "main.js"), "w") as f:
        f.write(main_content)
    
    # 创建测试组件
    os.makedirs(os.path.join(test_source_path, "assets", "scripts"), exist_ok=True)
    component_content = """cc.Class({
    name: 'TestComponent',
    extends: cc.Component,
    
    properties: {
        testProperty: {
            default: 0,
            type: cc.Integer
        }
    },
    
    onLoad() {
        console.log('TestComponent onLoad');
    },
    
    start() {
        console.log('TestComponent start');
    }
});
"""
    with open(os.path.join(test_source_path, "assets", "scripts", "TestComponent.js"), "w") as f:
        f.write(component_content)
    
    print("测试项目结构创建完成")

def run_test():
    """运行测试"""
    print(f"\n开始测试逆向引擎...")
    print(f"源路径: {test_source_path}")
    print(f"输出路径: {test_output_path}")
    
    # 清理旧的输出目录
    if os.path.exists(test_output_path):
        shutil.rmtree(test_output_path)
    
    # 设置命令行参数
    sys.argv = [
        "main.py",
        "--path", test_source_path,
        "--output", test_output_path,
        "--verbose"
    ]
    
    try:
        # 运行主函数
        cli()
        print("\n测试成功完成！")
        
        # 检查输出目录结构
        print("\n输出目录结构：")
        for root, dirs, files in os.walk(test_output_path):
            level = root.replace(test_output_path, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
    except Exception as e:
        print(f"\n测试失败：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_test_project()
    run_test()
