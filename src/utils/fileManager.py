#!/usr/bin/env python3
"""
文件管理工具
"""

import os
import shutil
from tqdm import tqdm

class FileManager:
    """文件管理类"""
    
    def copyFile(self, src, dst, show_progress=False):
        """
        复制文件
        
        Args:
            src (str): 源文件路径
            dst (str): 目标文件路径
            show_progress (bool): 是否显示进度条
        """
        # 确保目标目录存在
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
    
    def copyDirectory(self, src, dst, show_progress=False):
        """
        复制目录
        
        Args:
            src (str): 源目录路径
            dst (str): 目标目录路径
            show_progress (bool): 是否显示进度条
        """
        # 确保目标目录存在
        os.makedirs(dst, exist_ok=True)
        
        # 获取文件列表
        files = []
        for root, _, filenames in os.walk(src):
            for filename in filenames:
                files.append(os.path.join(root, filename))
        
        # 复制文件
        if show_progress:
            for src_file in tqdm(files, desc="复制文件"):
                rel_path = os.path.relpath(src_file, src)
                dst_file = os.path.join(dst, rel_path)
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                shutil.copy2(src_file, dst_file)
        else:
            shutil.copytree(src, dst, dirs_exist_ok=True)
    
    def writeFile(self, path, content):
        """
        写入文件
        
        Args:
            path (str): 文件路径
            content (str or bytes): 文件内容
        """
        # 确保目标目录存在
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        if isinstance(content, bytes):
            with open(path, "wb") as f:
                f.write(content)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
    
    def readFile(self, path, mode="r"):
        """
        读取文件
        
        Args:
            path (str): 文件路径
            mode (str): 读取模式
        
        Returns:
            str or bytes: 文件内容
        """
        with open(path, mode) as f:
            return f.read()
    
    def deleteFile(self, path):
        """
        删除文件
        
        Args:
            path (str): 文件路径
        """
        if os.path.exists(path):
            os.remove(path)
    
    def deleteDirectory(self, path):
        """
        删除目录
        
        Args:
            path (str): 目录路径
        """
        if os.path.exists(path):
            shutil.rmtree(path)
    
    def cleanDirectory(self, path):
        """
        清理目录内容
        
        Args:
            path (str): 目录路径
        """
        if os.path.exists(path):
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                else:
                    shutil.rmtree(item_path)
    
    def getFiles(self, directory, pattern=None):
        """
        获取目录下的所有文件
        
        Args:
            directory (str): 目录路径
            pattern (str): 文件名模式（可选）
        
        Returns:
            list: 文件路径列表
        """
        files = []
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                if pattern is None or filename.endswith(pattern):
                    files.append(os.path.join(root, filename))
        return files
    
    def getDirectories(self, directory):
        """
        获取目录下的所有子目录
        
        Args:
            directory (str): 目录路径
        
        Returns:
            list: 目录路径列表
        """
        dirs = []
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                dirs.append(item_path)
        return dirs

# 创建全局实例
fileManager = FileManager()
