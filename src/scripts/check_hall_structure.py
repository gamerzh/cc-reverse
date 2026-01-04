#!/usr/bin/env python3
"""
检查hall目录的结构
"""

import os

def check_hall_directory(build_dir):
    hall_path = os.path.join(build_dir, 'assets', 'hall')
    print(f"检查目录: {hall_path}")
    
    if not os.path.exists(hall_path):
        print(f"目录不存在: {hall_path}")
        return
    
    # 遍历hall目录
    print(f"\n=== hall目录内容 ===")
    for root, dirs, files in os.walk(hall_path):
        level = root.replace(hall_path, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")
    
    # 搜索整个build目录中是否有LobbyScene相关文件
    print(f"\n=== 搜索整个build目录中的LobbyScene文件 ===")
    lobby_files = []
    for root, _, files in os.walk(build_dir):
        for file in files:
            if 'lobbyscene' in file.lower():
                lobby_files.append(os.path.join(root, file))
    
    if lobby_files:
        print(f"找到 {len(lobby_files)} 个LobbyScene相关文件:")
        for file_path in lobby_files:
            print(f"  {file_path}")
    else:
        print("未找到LobbyScene相关文件")
    
    # 搜索整个build目录中是否有.fire或.scene文件
    print(f"\n=== 搜索整个build目录中的场景文件 ===")
    scene_files = []
    for root, _, files in os.walk(build_dir):
        for file in files:
            if file.endswith('.fire') or file.endswith('.scene'):
                scene_files.append(os.path.join(root, file))
    
    if scene_files:
        print(f"找到 {len(scene_files)} 个场景文件:")
        for file_path in scene_files:
            print(f"  {file_path}")
    else:
        print("未找到.fire或.scene文件")
    
    # 检查settings.js或settings.json文件，可能包含场景信息
    print(f"\n=== 检查游戏设置文件 ===")
    settings_files = []
    for root, _, files in os.walk(build_dir):
        for file in files:
            if file == 'settings.js' or file == 'settings.json':
                settings_files.append(os.path.join(root, file))
    
    for settings_file in settings_files:
        print(f"\n检查设置文件: {settings_file}")
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 搜索LobbyScene相关内容
            if 'LobbyScene' in content:
                print(f"找到LobbyScene相关内容:")
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'LobbyScene' in line:
                        start = max(0, i - 2)
                        end = min(len(lines), i + 3)
                        for j in range(start, end):
                            print(f"  {j+1}: {lines[j]}")
        except Exception as e:
            print(f"处理设置文件失败: {e}")

def main():
    build_dir = r"C:\Workflow\xsh5\build\web-mobile"
    check_hall_directory(build_dir)

if __name__ == "__main__":
    main()