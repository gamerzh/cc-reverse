#!/usr/bin/env python3
"""
验证修改的逻辑：根据当前的 output，推理修改应该产生的结果
"""
import json
import os

config_path = r'C:\GitHub\cc-reverse\output\assets\a\config.c09f6.json'

with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

print("\n=== File Routing Analysis ===\n")

# UUID to Path mapping
uuids = config['uuids']
paths_obj = config['paths']

# 查找 abab - 001 prefab
target_uuid = uuids[3]  # UUID for index 3
target_path = paths_obj['3'][0]  # Path for index 3

print(f"Target: abab - 001.prefab")
print(f"  UUID[3]: {target_uuid}")
print(f"  Path[3]: {target_path}")
print(f"  Expected subdirectory: {os.path.dirname(target_path) or '(root)'}")
print(f"  Expected output: assets/a/{target_path}.prefab")

# 验证版本映射
print(f"\nVersion import mapping:")
vImport = config['versions']['import']
for i in range(0, len(vImport), 2):
    idx = vImport[i]
    hash_val = vImport[i + 1]
    if idx == 3:
        print(f"  Index 3 -> import hash: {hash_val}")

# 验证 packs
print(f"\nPacks mapping:")
for hash_key, indices in config['packs'].items():
    if 3 in indices:
        print(f"  importHash '{hash_key}' includes indices: {indices}")

print("\n=== Code Flow Simulation ===\n")

print("When processing import file with hash '83dee':")
print("  1. importMap.get('83dee') -> { uuid: '4fyraXpfdGZYZ9t+2ao7YI', ... }")
print("  2. assetId = '4fyraXpfdGZYZ9t+2ao7YI'")
print("  3. uuidPathMap.get('4fyraXpfdGZYZ9t+2ao7YI') -> { path: '003/abab - 001', ... }")
print("  4. derivedPath = '003/abab - 001'")
print("  5. derivedName = 'abab - 001'")
print("  6. In savePrefabFile:")
print("     - derivedSubdir = dirname('003/abab - 001') = '003'")
print("     - dir = path.join('assets', 'a', '003')")
print("     - Final path: assets/a/003/abab - 001.prefab")
