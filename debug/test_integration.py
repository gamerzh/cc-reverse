#!/usr/bin/env python3
"""
创建集成测试项目，模拟Cocos Creator Web输出结构
"""

import os
import json
import shutil

# 测试项目路径
integration_test_path = "integration_test_project"
test_output_path = "integration_test_output"

# 创建集成测试项目
def create_integration_test_project():
    """创建集成测试项目"""
    print("创建集成测试项目...")
    
    # 清理旧项目
    if os.path.exists(integration_test_path):
        shutil.rmtree(integration_test_path)
    
    # 创建基本目录结构
    os.makedirs(os.path.join(integration_test_path, "src"), exist_ok=True)
    os.makedirs(os.path.join(integration_test_path, "assets"), exist_ok=True)
    os.makedirs(os.path.join(integration_test_path, "assets", "scripts"), exist_ok=True)
    os.makedirs(os.path.join(integration_test_path, "assets", "textures"), exist_ok=True)
    os.makedirs(os.path.join(integration_test_path, "assets", "sounds"), exist_ok=True)
    os.makedirs(os.path.join(integration_test_path, "assets", "animations"), exist_ok=True)
    
    # 创建settings.js
    settings_content = """window._CCSettings = {
    debugMode: 0,
    jsList: [
        "assets/scripts/Player.js"
    ],
    scenes: [
        {
            "url": "assets/scenes/GameScene.fire",
            "uuid": "scene_123456"
        }
    ],
    paths: {
        "audio_bgm": ["audio/bgm.mp3"],
        "texture_player": ["textures/player.png"],
        "anim_player": ["animations/player_anim.json"]
    },
    types: [
        "cc.AudioClip",
        "cc.Texture2D",
        "cc.AnimationClip"
    ]
};
"""
    with open(os.path.join(integration_test_path, "src", "settings.js"), "w") as f:
        f.write(settings_content)
    
    # 创建main.js
    main_content = """console.log("Cocos Creator Integration Test");
cc.game.run();
"""
    with open(os.path.join(integration_test_path, "main.js"), "w") as f:
        f.write(main_content)
    
    # 创建Player.js组件
    player_content = """
cc.Class({
    name: 'Player',
    extends: cc.Component,
    
    properties: {
        speed: 100,
        jumpHeight: 200
    },
    
    onLoad() {
        console.log('Player onLoad');
    },
    
    start() {
        console.log('Player start');
    }
});
"""
    with open(os.path.join(integration_test_path, "assets", "scripts", "Player.js"), "w") as f:
        f.write(player_content)
    
    # 创建测试资源文件
    # 音频文件
    with open(os.path.join(integration_test_path, "assets", "sounds", "bgm.mp3"), "w") as f:
        f.write("// Audio placeholder")
    
    # 图片文件
    with open(os.path.join(integration_test_path, "assets", "textures", "player.png"), "w") as f:
        f.write("// Image placeholder")
    
    # 动画JSON文件
    animation_data = {
        "__type__": "cc.AnimationClip",
        "_name": "PlayerAnimation",
        "_duration": 1.0,
        "sample": 60,
        "speed": 1.0,
        "wrapMode": 1,
        "curveData": {}
    }
    with open(os.path.join(integration_test_path, "assets", "animations", "player_anim.json"), "w") as f:
        json.dump(animation_data, f, indent=2)
    
    print("集成测试项目创建完成！")

# 运行集成测试
def run_integration_test():
    """运行集成测试"""
    # 创建测试项目
    create_integration_test_project()
    
    # 清理旧输出
    if os.path.exists(test_output_path):
        shutil.rmtree(test_output_path)
    
    print(f"\n运行集成测试，源路径: {integration_test_path}")
    print(f"输出路径: {test_output_path}")
    
    # 运行主工具
    import subprocess
    result = subprocess.run([
        "python", "-m", "main.main",
        "--path", integration_test_path,
        "--output", test_output_path,
        "--verbose"
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("\n错误输出:")
        print(result.stderr)
    
    print(f"\n集成测试完成，退出码: {result.returncode}")
    
    # 检查输出结果
    if result.returncode == 0:
        print("\n输出目录结构:")
        for root, dirs, files in os.walk(test_output_path):
            level = root.replace(test_output_path, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files[:5]:  # 只显示前5个文件
                print(f"{subindent}{file}")
            if len(files) > 5:
                print(f"{subindent}... 等 {len(files)} 个文件")
    
    return result.returncode

if __name__ == "__main__":
    run_integration_test()
