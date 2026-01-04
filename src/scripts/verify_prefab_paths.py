#!/usr/bin/env python3
import json
import os
import sys

# 验证Prefab文件路径是否正确
def verify_prefab_paths(config_file, output_dir):
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 获取资源类型映射
        types = config.get('types', [])
        paths_dict = config.get('paths', {})
        
        # 查找Prefab类型索引
        prefab_type_index = None
        for i, type_name in enumerate(types):
            if type_name == 'cc.Prefab':
                prefab_type_index = i
                break
        
        if prefab_type_index is not None:
            print(f"Prefab类型索引: {prefab_type_index}")
            print("\n验证Prefab文件路径:")
            
            # 遍历所有Prefab资源
            count = 0
            for path_id, path_info in paths_dict.items():
                if isinstance(path_info, list) and len(path_info) > 1 and path_info[1] == prefab_type_index:
                    prefab_path = path_info[0]
                    
                    # 构建输出路径
                    output_assets_path = os.path.join(output_dir, 'assets')
                    prefab_file_path = os.path.join(output_assets_path, prefab_path + '.prefab')
                    
                    # 检查文件是否存在
                    file_exists = os.path.exists(prefab_file_path)
                    
                    print(f"原始路径: {prefab_path}")
                    print(f"生成路径: {prefab_file_path}")
                    print(f"文件存在: {file_exists}")
                    print()
                    
                    count += 1
                    if count >= 10:
                        break
        else:
            print("未找到cc.Prefab类型")
            
    except Exception as e:
        print(f"验证失败: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python verify_prefab_paths.py <config_file_path> <output_dir>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    output_dir = sys.argv[2]
    verify_prefab_paths(config_file, output_dir)
