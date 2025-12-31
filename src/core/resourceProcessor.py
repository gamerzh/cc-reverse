#!/usr/bin/env python3
"""
资源处理器
"""

import os
import filetype

class ResourceProcessor:
    """资源处理器类"""
    
    def __init__(self):
        """初始化"""
        self.processed_resources = []
    
    def processResources(self):
        """
        处理资源
        """
        from src.utils.logger import logger
        from src.core.reverseEngine import global_paths, global_settings
        import os
        
        logger().debug("开始处理资源...")
        
        # 获取资源目录路径
        res_path = global_paths.get('res', '')
        source_path = global_paths.get('source', '')
        
        # 尝试多种资源目录位置
        asset_paths = [
            res_path,  # 默认检测到的资源路径
            os.path.join(source_path, 'assets'),  # 直接在项目根目录下的assets
            os.path.join(source_path, 'res')  # 直接在项目根目录下的res
        ]
        
        # 找到第一个存在的资源目录
        valid_asset_path = None
        for path in asset_paths:
            if path and os.path.exists(path):
                valid_asset_path = path
                logger().info(f"使用资源目录: {valid_asset_path}")
                break
        
        if not valid_asset_path:
            logger().warn("未找到资源目录")
            return
        
        # 遍历资源目录
        for root, _, files in os.walk(valid_asset_path):
            for file in files:
                file_path = os.path.join(root, file)
                # 计算相对于资源目录的路径
                rel_path = os.path.relpath(file_path, valid_asset_path)
                
                # 处理不同类型的资源
                self._processResource(file_path, rel_path)
    
    def _processResource(self, file_path, rel_path):
        """
        处理单个资源
        
        Args:
            file_path (str): 资源文件路径
            rel_path (str): 资源相对路径
        """
        from src.utils.logger import logger
        from src.core.reverseEngine import global_paths
        from src.utils.fileManager import fileManager
        
        # 检测文件类型
        kind = filetype.guess(file_path)
        if kind:
            logger().debug(f"处理资源: {rel_path}, 类型: {kind.mime}")
        else:
            logger().debug(f"处理资源: {rel_path}, 类型: 未知")
        
        # 资源输出路径
        output_path = os.path.join(global_paths.get('output', ''), 'assets', rel_path)
        
        # 复制资源到输出目录
        fileManager.copyFile(file_path, output_path)
        
        # 添加到已处理资源列表
        self.processed_resources.append({
            'source': file_path,
            'target': output_path,
            'type': kind.mime if kind else 'unknown',
            'relative_path': rel_path
        })
    
    def getProcessedResources(self):
        """
        获取已处理的资源列表
        
        Returns:
            list: 已处理的资源列表
        """
        return self.processed_resources

# 创建全局实例
resourceProcessor = ResourceProcessor()
