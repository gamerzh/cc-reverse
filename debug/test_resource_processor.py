#!/usr/bin/env python3
"""
测试资源处理器的功能
"""

import os
import shutil
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 测试项目路径
test_project_path = "debug_test_project"
test_output_path = "debug_test_output"

# 创建测试项目
def create_test_project():
    """创建测试项目"""
    print("创建测试项目...")
    
    # 清理旧项目
    if os.path.exists(test_project_path):
        shutil.rmtree(test_project_path)
    
    # 创建基本目录
    os.makedirs(os.path.join(test_project_path, "res"), exist_ok=True)
    os.makedirs(os.path.join(test_project_path, "res", "audio"), exist_ok=True)
    os.makedirs(os.path.join(test_project_path, "res", "textures"), exist_ok=True)
    os.makedirs(os.path.join(test_project_path, "res", "animations"), exist_ok=True)
    
    # 创建测试音频文件
    with open(os.path.join(test_project_path, "res", "audio", "bgm.mp3"), "w") as f:
        f.write("// Audio placeholder")
    
    # 创建测试图片文件
    with open(os.path.join(test_project_path, "res", "textures", "player.png"), "w") as f:
        f.write("// Image placeholder")
    
    # 创建测试动画JSON文件
    animation_data = {
        "__type__": "cc.AnimationClip",
        "_name": "PlayerAnimation",
        "_duration": 1.0,
        "sample": 60,
        "speed": 1.0,
        "wrapMode": 1,
        "curveData": {}
    }
    with open(os.path.join(test_project_path, "res", "animations", "player_anim.json"), "w") as f:
        json.dump(animation_data, f, indent=2)
    
    print("测试项目创建完成！")

# 测试资源处理器
def test_resource_processor():
    """测试资源处理器"""
    import sys
    import os
    # 添加项目根目录到Python路径
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from resources_reverse.resourceProcessor import ResourceProcessor
    
    print("\n测试资源处理器...")
    
    # 创建测试项目
    create_test_project()
    
    # 清理旧输出
    if os.path.exists(test_output_path):
        shutil.rmtree(test_output_path)
    
    # 配置
    paths = {
        "res": os.path.join(test_project_path, "res"),
        "output": test_output_path
    }
    
    settings = {
        "subpackages": {},
        "uuids": {}
    }
    
    # 创建资源处理器实例
    processor = ResourceProcessor()
    
    try:
        # 处理资源
        processor.process_resources(paths, settings)
        
        print("\n资源处理完成！")
        
        # 显示输出结果
        print("\n输出目录结构:")
        for root, dirs, files in os.walk(test_output_path):
            level = root.replace(test_output_path, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
        
        print("\n测试成功！")
        return True
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理测试项目
        shutil.rmtree(test_project_path)
        shutil.rmtree(test_output_path)

if __name__ == "__main__":
    import json
    test_resource_processor()
