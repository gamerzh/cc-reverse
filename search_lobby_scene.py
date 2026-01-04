#!/usr/bin/env python3
"""
分析编译后的hall目录，查找LobbyScene相关的资源文件
"""

import os
import json
import sys

def search_lobby_scene_resources(build_dir):
    """
    搜索编译后的hall目录中与LobbyScene相关的资源文件
    """
    hall_path = os.path.join(build_dir, 'assets', 'hall')
    
    if not os.path.exists(hall_path):
        print(f"hall目录不存在: {hall_path}")
        return
    
    print(f"搜索 {hall_path} 目录中的LobbyScene相关资源...")
    
    # 首先检查hall目录下的config.json文件
    config_files = []
    for file in os.listdir(hall_path):
        if file.startswith('config.') and file.endswith('.json'):
            config_files.append(os.path.join(hall_path, file))
    
    if config_files:
        for config_file in config_files:
            print(f"\n=== 分析配置文件: {config_file} ===")
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                types = config.get('types', [])
                paths = config.get('paths', {})
                uuids = config.get('uuids', [])
                
                print(f"资源类型列表: {types}")
                print(f"UUID数量: {len(uuids)}")
                
                # 搜索所有路径中是否有Lobby相关的资源
                lobby_paths = []
                for path_id, path_info in paths.items():
                    if isinstance(path_info, list) and len(path_info) > 0:
                        resource_path = path_info[0]
                        if 'lobby' in resource_path.lower():
                            lobby_paths.append((path_id, path_info))
                
                if lobby_paths:
                    print(f"找到 {len(lobby_paths)} 个Lobby相关路径:")
                    for path_id, path_info in lobby_paths:
                        print(f"  {path_id}: {path_info}")
                
                # 搜索所有路径中是否有Scene相关的资源
                scene_paths = []
                for path_id, path_info in paths.items():
                    if isinstance(path_info, list) and len(path_info) > 1:
                        type_index = path_info[1]
                        if type_index < len(types):
                            type_name = types[type_index]
                            if 'scene' in type_name.lower():
                                scene_paths.append((path_id, path_info, type_name))
                
                if scene_paths:
                    print(f"找到 {len(scene_paths)} 个Scene相关路径:")
                    for path_id, path_info, type_name in scene_paths:
                        print(f"  {path_id}: {path_info} (类型: {type_name})")
                
            except Exception as e:
                print(f"处理配置文件 {config_file} 失败: {e}")
    
    # 检查hall/import目录下的所有JSON文件，看看是否有场景相关的内容
    import_path = os.path.join(hall_path, 'import')
    if os.path.exists(import_path):
        print(f"\n=== 搜索 {import_path} 目录中的JSON文件 ===")
        scene_json_files = []
        
        for root, _, files in os.walk(import_path):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = json.load(f)
                        
                        # 检查是否为场景相关的JSON文件
                        if isinstance(content, list) and len(content) > 0:
                            first_item = content[0]
                            if isinstance(first_item, dict) and first_item.get('__type__') == 'cc.Scene':
                                scene_json_files.append((file_path, content))
                                print(f"找到场景文件: {file_path}")
                            elif isinstance(first_item, dict) and 'scene' in first_item.get('__type__', '').lower():
                                scene_json_files.append((file_path, content))
                                print(f"找到场景相关文件: {file_path}")
                    except Exception as e:
                        # 忽略解析错误
                        pass
        
        if scene_json_files:
            print(f"\n=== 分析找到的场景文件 ===")
            for file_path, content in scene_json_files[:2]:  # 只显示前2个文件的详细信息
                print(f"\n文件: {file_path}")
                print(f"文件结构: 列表长度 = {len(content)}")
                if len(content) > 0:
                    first_item = content[0]
                    print(f"第一个元素类型: {first_item.get('__type__')}")
                    print(f"第一个元素名称: {first_item.get('_name')}")
                    print(f"第一个元素属性: {list(first_item.keys())[:10]}...")
    
    print(f"\n=== 搜索完成 ===")

def main():
    if len(sys.argv) != 2:
        print("Usage: python search_lobby_scene.py <build_directory>")
        sys.exit(1)
    
    build_dir = sys.argv[1]
    if not os.path.exists(build_dir):
        print(f"目录不存在: {build_dir}")
        sys.exit(1)
    
    search_lobby_scene_resources(build_dir)

if __name__ == "__main__":
    main()