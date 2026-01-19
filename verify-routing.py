#!/usr/bin/env python3
import json
import sys

# 加载 config
config_path = 'output/assets/a/config.c09f6.json'
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

print("\n=== UUID to Path Mapping ===\n")

# 构建 uuid -> path 映射（模拟代码逻辑）
uuids = config.get('uuids', [])
paths_data = config.get('paths', {})

uuid_to_path = {}
if isinstance(paths_data, dict):
    for idx_str, item in paths_data.items():
        try:
            idx = int(idx_str)
        except ValueError:
            continue
        
        if idx < len(uuids):
            uuid = uuids[idx]
            path = item[0] if isinstance(item, list) else item
            uuid_to_path[uuid] = path
            
            # 打印包含 "003" 的映射
            if '003' in path:
                print(f"UUID: {uuid}")
                print(f"Path: {path}")
                print()

print("\n=== Derived File Paths ===\n")

# 模拟 processSerializedFile 的逻辑
# 假设导入的是索引3（abab - 001 prefab）
print("Expected routing for abab - 001.prefab:")
print(f"  Index: 3")
print(f"  UUID: {uuids[3] if 3 < len(uuids) else 'N/A'}")
print(f"  Path: {paths_data['3'][0] if '3' in paths_data else 'N/A'}")
print(f"  Subdirectory: 003")
print(f"  Output location: assets/a/003/abab - 001.prefab")
