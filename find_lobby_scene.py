#!/usr/bin/env python3
"""
分析编译后的资源，查找hall/LobbyScene.fire对应的资源
"""

import os
import json
import sys

def search_for_lobby_scene(config_files):
    """
    在配置文件中搜索hall/LobbyScene相关的资源
    """
    for config_file in config_files:
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            print(f"\n=== 分析配置文件: {config_file} ===")
            
            # 检查types字段
            types = config.get('types', [])
            print(f"资源类型列表: {types}")
            
            # 检查是否有cc.Scene类型
            if 'cc.Scene' in types:
                scene_type_index = types.index('cc.Scene')
                print(f"cc.Scene类型索引: {scene_type_index}")
            
            # 检查paths字段中是否有hall相关路径
            paths = config.get('paths', {})
            found_hall_paths = []
            for path_id, path_info in paths.items():
                if isinstance(path_info, list) and len(path_info) > 0:
                    resource_path = path_info[0]
                    if 'hall' in resource_path.lower():
                        found_hall_paths.append((path_id, path_info))
            
            if found_hall_paths:
                print(f"找到 {len(found_hall_paths)} 个hall相关路径:")
                for path_id, path_info in found_hall_paths:
                    print(f"  {path_id}: {path_info}")
            
            # 检查uuids字段
            uuids = config.get('uuids', [])
            print(f"UUID数量: {len(uuids)}")
            
        except Exception as e:
            print(f"处理配置文件 {config_file} 失败: {e}")

def find_config_files(directory):
    """
    查找目录下所有的config.json文件
    """
    config_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith('config.') and file.endswith('.json'):
                config_files.append(os.path.join(root, file))
    return config_files

def main():
    if len(sys.argv) != 2:
        print("Usage: python find_lobby_scene.py <build_directory>")
        sys.exit(1)
    
    build_dir = sys.argv[1]
    if not os.path.exists(build_dir):
        print(f"目录不存在: {build_dir}")
        sys.exit(1)
    
    print(f"正在搜索 {build_dir} 目录下的config.json文件...")
    config_files = find_config_files(build_dir)
    print(f"找到 {len(config_files)} 个config.json文件")
    
    search_for_lobby_scene(config_files)
    
    # 同时检查是否有直接的lobby相关文件
    print(f"\n=== 搜索直接的lobby相关文件 ===")
    lobby_files = []
    for root, _, files in os.walk(build_dir):
        for file in files:
            if 'lobby' in file.lower() or 'hall' in file.lower():
                file_path = os.path.join(root, file)
                lobby_files.append(file_path)
    
    if lobby_files:
        print(f"找到 {len(lobby_files)} 个lobby/hall相关文件:")
        for file_path in lobby_files[:20]:  # 只显示前20个
            print(f"  {file_path}")
        if len(lobby_files) > 20:
            print(f"  ... 还有 {len(lobby_files) - 20} 个文件未显示")
    
    # 检查是否有scene相关的json文件
    print(f"\n=== 搜索scene相关的json文件 ===")
    scene_files = []
    for root, _, files in os.walk(build_dir):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = json.load(f)
                    # 检查是否为场景文件结构
                    if isinstance(content, list) and len(content) > 0:
                        first_item = content[0]
                        if isinstance(first_item, dict) and first_item.get('__type__') == 'cc.Scene':
                            scene_files.append(file_path)
                except:
                    pass
    
    if scene_files:
        print(f"找到 {len(scene_files)} 个场景文件:")
        for file_path in scene_files:
            print(f"  {file_path}")

if __name__ == "__main__":
    main()