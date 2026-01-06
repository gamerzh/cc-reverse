#!/usr/bin/env python3
"""
简单测试脚本，用于验证资源处理器修复
"""

import os
import shutil

# 测试项目路径
test_project_path = "simple_test_project"
test_output_path = "simple_test_output"

# 创建简单测试项目
def create_simple_project():
    """创建简单测试项目"""
    print("创建简单测试项目...")
    
    # 清理旧项目
    if os.path.exists(test_project_path):
        shutil.rmtree(test_project_path)
    
    # 创建基本目录
    os.makedirs(os.path.join(test_project_path, "src"), exist_ok=True)
    os.makedirs(os.path.join(test_project_path, "assets"), exist_ok=True)
    os.makedirs(os.path.join(test_project_path, "assets", "scripts"), exist_ok=True)
    os.makedirs(os.path.join(test_project_path, "assets", "textures"), exist_ok=True)
    os.makedirs(os.path.join(test_project_path, "assets", "sounds"), exist_ok=True)
    
    # 创建settings.js
    with open(os.path.join(test_project_path, "src", "settings.js"), "w") as f:
        f.write("""window._CCSettings = {
    jsList: [
        "assets/scripts/TestComponent.js"
    ],
    debugMode: 0
};
""")
    
    # 创建main.js
    with open(os.path.join(test_project_path, "main.js"), "w") as f:
        f.write("console.log('Cocos Creator Project');")
    
    # 创建测试组件
    with open(os.path.join(test_project_path, "assets", "scripts", "TestComponent.js"), "w") as f:
        f.write("""cc.Class({
    name: 'TestComponent',
    extends: cc.Component,
    
    properties: {
        testProperty: 100
    },
    
    onLoad() {
        console.log('TestComponent onLoad');
    }
});
""")
    
    # 创建图片资源（空文件）
    with open(os.path.join(test_project_path, "assets", "textures", "test.png"), "w") as f:
        f.write("// image placeholder")
    
    # 创建音频资源（空文件）
    with open(os.path.join(test_project_path, "assets", "sounds", "test.mp3"), "w") as f:
        f.write("// audio placeholder")
    
    print("简单测试项目创建完成！")

# 运行测试
def run_test():
    """运行测试"""
    import sys
    
    # 清理旧输出
    if os.path.exists(test_output_path):
        shutil.rmtree(test_output_path)
    
    print(f"\n运行逆向工具，源路径: {test_project_path}")
    print(f"输出路径: {test_output_path}")
    
    # 设置命令行参数
    sys.argv = [
        "main.py",
        "--path", test_project_path,
        "--output", test_output_path,
        "--verbose"
    ]
    
    # 添加项目路径
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # 导入主函数
    from main.main import cli
    
    try:
        cli()
        print("\n测试成功完成！")
        
        # 显示输出结果
        print(f"\n输出目录结构: {test_output_path}")
        for root, dirs, files in os.walk(test_output_path):
            level = root.replace(test_output_path, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_simple_project()
    run_test()
