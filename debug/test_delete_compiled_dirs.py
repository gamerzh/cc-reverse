#!/usr/bin/env python3
"""
测试删除编译后目录功能
"""

import os
import shutil
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main.utils.fileManager import fileManager

# 创建测试目录结构
test_root = "c:/GitHub/cc-reverse/test_delete_compiled_dirs"

# 清理旧的测试目录
if os.path.exists(test_root):
    shutil.rmtree(test_root)

# 创建测试目录结构，包括import和native目录
os.makedirs(os.path.join(test_root, "assets", "fhpoker", "import", "textures"))
os.makedirs(os.path.join(test_root, "assets", "fhpoker", "native", "02"))
os.makedirs(os.path.join(test_root, "assets", "fhpoker", "textures", "image"))
os.makedirs(os.path.join(test_root, "assets", "othermodule", "import"))
os.makedirs(os.path.join(test_root, "assets", "othermodule", "native"))

# 在非编译目录中创建一些文件
os.makedirs(os.path.join(test_root, "assets", "fhpoker", "textures", "non_empty"))
with open(os.path.join(test_root, "assets", "fhpoker", "textures", "non_empty", "test.txt"), "w") as f:
    f.write("test content")

# 打印初始目录结构
print("初始目录结构:")
for root, dirs, files in os.walk(test_root):
    level = root.replace(test_root, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f"{subindent}{file}")

# 测试删除编译后目录
print("\n开始删除编译后目录(import和native)...")
fileManager.deleteDirectoriesByName(os.path.join(test_root, "assets"), ["import", "native"])

# 打印删除后的目录结构
print("\n删除编译后目录后的结构:")
for root, dirs, files in os.walk(test_root):
    level = root.replace(test_root, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f"{subindent}{file}")

# 测试删除空目录
print("\n开始删除空目录...")
fileManager.deleteEmptyDirectories(os.path.join(test_root, "assets"))

# 打印最终目录结构
print("\n最终目录结构:")
for root, dirs, files in os.walk(test_root):
    level = root.replace(test_root, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f"{subindent}{file}")

# 清理测试目录
if os.path.exists(test_root):
    shutil.rmtree(test_root)
    print("\n测试完成，已清理测试目录")
