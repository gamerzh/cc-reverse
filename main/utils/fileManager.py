#!/usr/bin/env python3
"""
fileManager.py - 文件管理工具
"""

import os
import shutil

class fileManager:
    """文件管理器类"""

    @staticmethod
    def deleteDirectoriesByName(root_path, dir_names):
        """
        删除指定名称的目录

        Args:
            root_path (str): 根目录路径
            dir_names (list): 要删除的目录名称列表
        """
        for root, dirs, files in os.walk(root_path, topdown=False):
            for dir_name in dirs:
                if dir_name in dir_names:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        shutil.rmtree(dir_path)
                        print(f"已删除目录: {dir_path}")
                    except Exception as e:
                        print(f"删除目录失败 {dir_path}: {e}")

    @staticmethod
    def deleteEmptyDirectories(root_path):
        """
        删除空目录

        Args:
            root_path (str): 根目录路径
        """
        for root, dirs, files in os.walk(root_path, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                        print(f"已删除空目录: {dir_path}")
                except Exception as e:
                    pass  # 目录不为空或已被删除