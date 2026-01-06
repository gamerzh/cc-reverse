#!/usr/bin/env python3
"""
文件管理工具
"""

import os
import shutil
from tqdm import tqdm
from utils.logger import logger

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
        # 确保目标目录存在，跳过当前目录（空字符串）
        dst_dir = os.path.dirname(dst)
        if dst_dir:
            os.makedirs(dst_dir, exist_ok=True)
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
        # 确保目标目录存在，跳过当前目录（空字符串）
        dst_dir = os.path.dirname(path)
        if dst_dir:
            os.makedirs(dst_dir, exist_ok=True)
        
        if isinstance(content, bytes):
            with open(path, "wb") as f:
                f.write(content)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
    
    def readFile(self, path, mode="r", encoding="utf-8"):
        """
        读取文件
        
        Args:
            path (str): 文件路径
            mode (str): 读取模式
            encoding (str): 文本模式下的编码格式，默认utf-8
        
        Returns:
            str or bytes: 文件内容
        """
        if "b" in mode:
            # 二进制模式不需要编码
            with open(path, mode) as f:
                return f.read()
        else:
            # 文本模式使用指定编码
            with open(path, mode, encoding=encoding) as f:
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
    
    def deleteEmptyDirectories(self, directory, max_retries=3):
        """
        递归删除空目录
        
        Args:
            directory (str): 目录路径
            max_retries (int): 最大重试次数，用于处理并发目录变化
        
        Returns:
            bool: 目录是否被删除
        """
        logger().info(f"开始递归删除空目录: {directory}")
        
        # 递归处理，确保我们能处理深层嵌套的空目录
        def _delete_empty_dirs(path):
            if not os.path.exists(path):
                return True
            
            if not os.path.isdir(path):
                return False
            
            # 先处理所有子目录
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    _delete_empty_dirs(item_path)
            
            # 检查当前目录是否为空
            try:
                contents = os.listdir(path)
                logger().debug(f"目录 {path} 包含 {len(contents)} 个项目: {contents}")
                
                if not contents:
                    os.rmdir(path)
                    logger().info(f"已删除空目录: {path}")
                    return True
                else:
                    logger().debug(f"目录 {path} 不为空，跳过删除")
                    return False
            except Exception as e:
                logger().error(f"处理目录 {path} 时出错: {e}")
                return False
        
        # 重试多次，确保所有空目录都被删除
        for i in range(max_retries):
            logger().debug(f"第 {i+1} 次尝试删除空目录: {directory}")
            _delete_empty_dirs(directory)
            
            # 检查顶层目录是否还存在
            if not os.path.exists(directory):
                logger().info(f"顶层目录 {directory} 已被删除")
                return True
            
            # 检查顶层目录是否为空
            if not os.listdir(directory):
                try:
                    os.rmdir(directory)
                    logger().info(f"已删除顶层空目录: {directory}")
                    return True
                except Exception as e:
                    logger().error(f"删除顶层目录 {directory} 时出错: {e}")
        
        logger().info(f"空目录删除完成，剩余目录: {directory}")
        return False
    
    def deleteDirectoriesByName(self, directory, dir_names):
        """
        递归删除指定名称的目录
        
        Args:
            directory (str): 目录路径
            dir_names (list): 要删除的目录名称列表
        """
        logger().info(f"开始递归删除指定名称的目录: {directory}, 目录名: {dir_names}")
        
        if not os.path.exists(directory):
            logger().debug(f"目录不存在，跳过: {directory}")
            return
        
        if not os.path.isdir(directory):
            logger().debug(f"不是目录，跳过: {directory}")
            return
        
        # 处理当前目录的子目录
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                # 如果目录名在要删除的列表中，删除整个目录
                if item in dir_names:
                    logger().info(f"删除目录: {item_path}")
                    try:
                        shutil.rmtree(item_path)
                        logger().info(f"已删除目录: {item_path}")
                    except Exception as e:
                        logger().error(f"删除目录 {item_path} 时出错: {e}")
                else:
                    # 否则递归处理子目录
                    self.deleteDirectoriesByName(item_path, dir_names)
        
        logger().info(f"指定名称目录删除完成: {directory}")

# 创建全局实例
fileManager = FileManager()
