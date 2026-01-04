#!/usr/bin/env python3
"""
资源处理器
"""

import os
import filetype
import shutil

class ResourceProcessor:
    """资源处理器类"""
    
    def __init__(self):
        """初始化"""
        self.processed_resources = []
        self.resource_types = {
            'image': [
                'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 
                'image/webp', 'image/tiff'
            ],
            'audio': [
                'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/ogg',
                'audio/flac', 'audio/aac'
            ],
            'video': [
                'video/mp4', 'video/webm', 'video/ogg'
            ],
            'font': [
                'font/ttf', 'font/otf', 'application/font-sfnt',
                'application/vnd.ms-opentype'
            ],
            'text': [
                'text/plain', 'text/javascript', 'text/css', 'text/html'
            ],
            'json': [
                'application/json'
            ],
            'xml': [
                'application/xml', 'text/xml'
            ],
            'binary': [
                'application/octet-stream'
            ]
        }
    
    def processResources(self):
        """
        处理资源
        """
        from src.utils.logger import logger
        from src.core.reverseEngine import global_paths, global_settings
        import os
        
        logger().info("开始处理资源...")
        
        # 获取资源目录路径
        res_path = global_paths.get('res', '')
        source_path = global_paths.get('source', '')
        
        # 尝试多种资源目录位置
        asset_paths = [
            res_path,  # 默认检测到的资源路径
            os.path.join(source_path, 'assets'),  # 直接在项目根目录下的assets
            os.path.join(source_path, 'res'),  # 直接在项目根目录下的res
            os.path.join(source_path, 'src', 'assets'),  # src目录下的assets
            os.path.join(source_path, 'src', 'res')  # src目录下的res
        ]
        
        # 找到所有存在的资源目录
        valid_asset_paths = []
        for path in asset_paths:
            if path and os.path.exists(path):
                valid_asset_paths.append(path)
                logger().info(f"找到资源目录: {path}")
        
        if not valid_asset_paths:
            logger().warn("未找到资源目录")
            return
        
        # 处理每个资源目录
        for valid_asset_path in valid_asset_paths:
            # 遍历资源目录
            for root, _, files in os.walk(valid_asset_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # 计算相对于资源目录的路径
                    rel_path = os.path.relpath(file_path, valid_asset_path)
                    
                    # 处理不同类型的资源
                    self._processResource(file_path, rel_path, valid_asset_path)
        
        logger().info(f"资源处理完成，共处理 {len(self.processed_resources)} 个资源")
    
    def _processResource(self, file_path, rel_path, asset_root):
        """
        处理单个资源
        
        Args:
            file_path (str): 资源文件路径
            rel_path (str): 资源相对路径
            asset_root (str): 资源根目录
        """
        from src.utils.logger import logger
        from src.core.reverseEngine import global_paths
        from src.utils.fileManager import fileManager
        
        # 检测文件类型
        kind = filetype.guess(file_path)
        mime_type = kind.mime if kind else 'unknown'
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # 确定资源类型类别
        resource_category = self._determineResourceCategory(mime_type, file_ext)
        
        logger().debug(f"处理资源: {rel_path}, 类型: {mime_type}, 类别: {resource_category}")
        
        # 资源输出路径
        output_path = os.path.join(global_paths.get('output', ''), 'assets', rel_path)
        
        try:
            # 根据资源类型进行专门处理
            if resource_category == 'image':
                self._processImageResource(file_path, output_path)
            elif resource_category == 'audio':
                self._processAudioResource(file_path, output_path)
            elif resource_category == 'font':
                self._processFontResource(file_path, output_path)
            elif resource_category in ['json', 'text', 'xml']:
                self._processTextResource(file_path, output_path)
            else:
                # 默认处理
                fileManager.copyFile(file_path, output_path)
            
            # 添加到已处理资源列表
            self.processed_resources.append({
                'source': file_path,
                'target': output_path,
                'type': mime_type,
                'category': resource_category,
                'relative_path': rel_path,
                'file_ext': file_ext
            })
        except Exception as e:
            logger().error(f"处理资源 {rel_path} 失败: {e}")
    
    def _determineResourceCategory(self, mime_type, file_ext):
        """
        确定资源类型类别
        
        Args:
            mime_type (str): 文件MIME类型
            file_ext (str): 文件扩展名
        
        Returns:
            str: 资源类型类别
        """
        # 优先根据文件扩展名判断
        ext_to_category = {
            '.png': 'image',
            '.jpg': 'image',
            '.jpeg': 'image',
            '.gif': 'image',
            '.bmp': 'image',
            '.webp': 'image',
            '.tiff': 'image',
            '.mp3': 'audio',
            '.wav': 'audio',
            '.ogg': 'audio',
            '.flac': 'audio',
            '.aac': 'audio',
            '.mp4': 'video',
            '.webm': 'video',
            '.ttf': 'font',
            '.otf': 'font',
            '.js': 'text',
            '.json': 'json',
            '.xml': 'xml',
            '.css': 'text',
            '.html': 'text',
            '.txt': 'text'
        }
        
        if file_ext in ext_to_category:
            return ext_to_category[file_ext]
        
        # 根据MIME类型判断
        for category, mime_types in self.resource_types.items():
            if mime_type in mime_types:
                return category
        
        return 'binary'
    
    def _processImageResource(self, source_path, target_path):
        """
        处理图像资源
        
        Args:
            source_path (str): 源文件路径
            target_path (str): 目标文件路径
        """
        from src.utils.fileManager import fileManager
        # 确保目录存在
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        # 复制图像文件
        shutil.copy2(source_path, target_path)
    
    def _processAudioResource(self, source_path, target_path):
        """
        处理音频资源
        
        Args:
            source_path (str): 源文件路径
            target_path (str): 目标文件路径
        """
        from src.utils.fileManager import fileManager
        # 确保目录存在
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        # 复制音频文件
        shutil.copy2(source_path, target_path)
    
    def _processFontResource(self, source_path, target_path):
        """
        处理字体资源
        
        Args:
            source_path (str): 源文件路径
            target_path (str): 目标文件路径
        """
        from src.utils.fileManager import fileManager
        # 确保目录存在
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        # 复制字体文件
        shutil.copy2(source_path, target_path)
    
    def _processTextResource(self, source_path, target_path):
        """
        处理文本资源
        
        Args:
            source_path (str): 源文件路径
            target_path (str): 目标文件路径
        """
        from src.utils.fileManager import fileManager
        # 确保目录存在
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # 读取并复制文本文件
        content = fileManager.readFile(source_path)
        fileManager.writeFile(target_path, content)
    
    def _processBinaryResource(self, source_path, target_path):
        """
        处理二进制资源
        
        Args:
            source_path (str): 源文件路径
            target_path (str): 目标文件路径
        """
        from src.utils.fileManager import fileManager
        # 确保目录存在
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        # 复制二进制文件
        shutil.copy2(source_path, target_path)
    
    def getProcessedResources(self):
        """
        获取已处理的资源列表
        
        Returns:
            list: 已处理的资源列表
        """
        return self.processed_resources
    
    def getResourceStats(self):
        """
        获取资源统计信息
        
        Returns:
            dict: 资源统计信息
        """
        stats = {
            'total': len(self.processed_resources),
            'by_category': {}
        }
        
        for resource in self.processed_resources:
            category = resource['category']
            if category not in stats['by_category']:
                stats['by_category'][category] = 0
            stats['by_category'][category] += 1
        
        return stats

# 创建全局实例
resourceProcessor = ResourceProcessor()
