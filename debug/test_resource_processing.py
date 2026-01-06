#!/usr/bin/env python3
"""
测试资源处理逻辑
"""

import os
import shutil
import sys

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.resourceProcessor import ResourceProcessor

# 创建测试目录结构
test_root = "c:/GitHub/cc-reverse/test_resource_processing"
source_dir = os.path.join(test_root, "source")
output_dir = os.path.join(test_root, "output")

# 清理旧的测试目录
if os.path.exists(test_root):
    shutil.rmtree(test_root)

# 创建测试资源文件结构
os.makedirs(os.path.join(source_dir, "assets", "fhpoker", "textures", "image"))
os.makedirs(os.path.join(source_dir, "assets", "fhpoker", "audio"))
os.makedirs(os.path.join(source_dir, "assets", "fhpoker", "fonts"))

# 创建测试资源文件
with open(os.path.join(source_dir, "assets", "fhpoker", "textures", "image", "test1.png"), "wb") as f:
    f.write(b"PNG test data")

with open(os.path.join(source_dir, "assets", "fhpoker", "textures", "image", "test2.jpg"), "wb") as f:
    f.write(b"JPG test data")

with open(os.path.join(source_dir, "assets", "fhpoker", "audio", "test_sound.mp3"), "wb") as f:
    f.write(b"MP3 test data")

with open(os.path.join(source_dir, "assets", "fhpoker", "fonts", "test_font.ttf"), "wb") as f:
    f.write(b"TTF test data")

with open(os.path.join(source_dir, "assets", "fhpoker", "config.123.json"), "w") as f:
    f.write('{"types": ["cc.Prefab", "cc.Scene"], "paths": {"0": ["test/path"]}, "uuids": ["uuid-123"]}')

# 打印初始目录结构
print("初始源目录结构:")
for root, dirs, files in os.walk(source_dir):
    level = root.replace(source_dir, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f"{subindent}{file}")

# 初始化资源处理器
resource_processor = ResourceProcessor()

# 准备路径字典
paths = {
    'source': source_dir,
    'output': output_dir,
    'res': os.path.join(source_dir, 'assets')
}

# 运行资源处理
print("\n开始资源处理...")
resource_processor.processResources(paths)

# 打印输出目录结构
print("\n输出目录结构:")
for root, dirs, files in os.walk(output_dir):
    level = root.replace(output_dir, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f"{subindent}{file}")

# 验证所有资源文件是否被正确处理
print("\n验证资源处理结果...")
source_files = []
for root, _, files in os.walk(source_dir):
    for file in files:
        if not file.startswith('config.') or not file.endswith('.json'):
            # 获取相对于source_dir/assets的路径
            asset_rel_path = os.path.relpath(os.path.join(root, file), os.path.join(source_dir, "assets"))
            source_files.append(asset_rel_path)

output_files = []
for root, _, files in os.walk(output_dir):
    for file in files:
        # 获取相对于output_dir/assets的路径
        asset_rel_path = os.path.relpath(os.path.join(root, file), os.path.join(output_dir, "assets"))
        output_files.append(asset_rel_path)

# 检查每个源文件是否在输出目录中
all_files_found = True
for source_file in source_files:
    if source_file in output_files:
        print(f"✅ 找到文件: assets/{source_file}")
    else:
        print(f"❌ 缺失文件: assets/{source_file}")
        all_files_found = False

if all_files_found:
    print("\n✅ 所有资源文件都被正确处理!")
else:
    print("\n❌ 部分资源文件未被处理!")

# 清理测试目录
if os.path.exists(test_root):
    shutil.rmtree(test_root)
    print("\n测试完成，已清理测试目录")
