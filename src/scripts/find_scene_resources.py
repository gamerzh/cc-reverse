#!/usr/bin/env python3
import os
import json

def find_scene_resources(source_path):
    """
    查找所有config.json文件中的cc.Scene资源
    """
    scene_found = False
    
    for root, dirs, files in os.walk(source_path):
        for file in files:
            if file.startswith('config.') and file.endswith('.json'):
                config_file = os.path.join(root, file)
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    types = config.get('types', [])
                    if 'cc.Scene' in types:
                        scene_found = True
                        print(f'在 {config_file} 中找到cc.Scene类型')
                        
                        scene_index = types.index('cc.Scene')
                        paths_dict = config.get('paths', {})
                        scene_count = 0
                        
                        for path_id, path_info in paths_dict.items():
                            if isinstance(path_info, list) and len(path_info) > 1 and path_info[1] == scene_index:
                                scene_path = path_info[0]
                                print(f'  场景路径: {scene_path}')
                                scene_count += 1
                                if scene_count >= 10:
                                    break
                        
                        print(f'  共找到 {scene_count} 个场景资源')
                    
                except Exception as e:
                    print(f'分析 {config_file} 失败: {e}')
    
    if not scene_found:
        print('未找到任何包含cc.Scene类型的config.json文件')

if __name__ == "__main__":
    source_path = "C:/Workflow/xsh5/build/web-mobile"
    find_scene_resources(source_path)
