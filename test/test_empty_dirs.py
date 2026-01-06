#!/usr/bin/env python3
"""
测试删除空目录功能
"""

import os
import sys
import shutil

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.fileManager import fileManager

# 创建测试目录结构
test_root = "c:/GitHub/cc-reverse/test_empty_dirs"

# 清理旧的测试目录
if os.path.exists(test_root):
    shutil.rmtree(test_root)

# 创建测试目录结构
os.makedirs(os.path.join(test_root, "assets", "audio"))
os.makedirs(os.path.join(test_root, "assets", "fonts"))
os.makedirs(os.path.join(test_root, "assets", "textures", "image"))
os.makedirs(os.path.join(test_root, "assets", "scenes"))
os.makedirs(os.path.join(test_root, "assets", "scripts"))
os.makedirs(os.path.join(test_root, "assets", "resources"))

# 创建一些非空目录
os.makedirs(os.path.join(test_root, "assets", "textures", "non_empty"))
with open(os.path.join(test_root, "assets", "textures", "non_empty", "test.txt"), "w") as f:
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

# 测试删除空目录
print("\n开始删除空目录...")
fileManager.deleteEmptyDirectories(os.path.join(test_root, "assets"))

# 打印删除后的目录结构
print("\n删除后的目录结构:")
if os.path.exists(test_root):
    for root, dirs, files in os.walk(test_root):
        level = root.replace(test_root, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")
else:
    print("测试根目录已被删除")

# 清理测试目录
if os.path.exists(test_root):
    shutil.rmtree(test_root)
    print("\n测试完成，已清理测试目录")
