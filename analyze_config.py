#!/usr/bin/env python3
import json
import sys
import os

# 分析config.json文件，查找Prefab资源
def analyze_config(config_file):
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 获取资源类型映射
        types = config.get('types', [])
        paths_dict = config.get('paths', {})
        
        print(f"文件: {config_file}")
        print(f"资源类型数量: {len(types)}")
        print(f"资源路径数量: {len(paths_dict)}")
        
        # 查找Prefab类型索引
        prefab_type_index = None
        for i, type_name in enumerate(types):
            if type_name == 'cc.Prefab':
                prefab_type_index = i
                break
        
        if prefab_type_index is not None:
            print(f"\nPrefab类型索引: {prefab_type_index}")
            print("\n前10个Prefab资源路径:")
            
            count = 0
            for path_id, path_info in paths_dict.items():
                if isinstance(path_info, list) and len(path_info) > 1 and path_info[1] == prefab_type_index:
                    prefab_path = path_info[0]
                    print(f"  {prefab_path}")
                    count += 1
                    if count >= 10:
                        break
        else:
            print("\n未找到cc.Prefab类型")
            
    except Exception as e:
        print(f"分析文件 {config_file} 失败: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python analyze_config.py <config_file_path>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    analyze_config(config_file)
