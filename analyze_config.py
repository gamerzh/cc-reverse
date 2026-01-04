#!/usr/bin/env python3
import json
import sys
import os

# 分析config.json文件，查找Prefab资源
def analyze_config(config_file, resource_type='cc.Prefab', limit=10):
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 获取资源类型映射
        types = config.get('types', [])
        paths_dict = config.get('paths', {})
        
        print(f"文件: {config_file}")
        print(f"资源类型数量: {len(types)}")
        print(f"资源路径数量: {len(paths_dict)}")
        
        print(f"\n所有资源类型:")
        for i, type_name in enumerate(types):
            print(f"  {i}: {type_name}")
        
        # 查找指定类型的资源索引
        resource_type_index = None
        for i, type_name in enumerate(types):
            if type_name == resource_type:
                resource_type_index = i
                break
        
        if resource_type_index is not None:
            print(f"\n{resource_type}类型索引: {resource_type_index}")
            print(f"\n前{limit}个{resource_type}资源路径:")
            
            count = 0
            for path_id, path_info in paths_dict.items():
                if isinstance(path_info, list) and len(path_info) > 1 and path_info[1] == resource_type_index:
                    resource_path = path_info[0]
                    print(f"  {resource_path}")
                    count += 1
                    if count >= limit:
                        break
        else:
            print(f"\n未找到{resource_type}类型")
        
        # 查找场景相关资源
        print("\n查找场景相关资源:")
        scene_count = 0
        for path_id, path_info in paths_dict.items():
            if isinstance(path_info, list) and len(path_info) > 0:
                resource_path = path_info[0]
                if 'scene' in resource_path.lower() or 'fire' in resource_path.lower():
                    print(f"  {resource_path} (类型索引: {path_info[1]})")
                    scene_count += 1
                    if scene_count >= limit:
                        break
        
        if scene_count == 0:
            print("  未找到场景相关资源")
            
    except Exception as e:
        print(f"分析文件 {config_file} 失败: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python analyze_config.py <config_file_path> [resource_type] [limit]")
        sys.exit(1)
    
    config_file = sys.argv[1]
    resource_type = sys.argv[2] if len(sys.argv) > 2 else 'cc.Prefab'
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    analyze_config(config_file, resource_type, limit)
