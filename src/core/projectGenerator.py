#!/usr/bin/env python3
"""
项目生成器
"""

import os
import json

class ProjectGenerator:
    """项目生成器类"""
    
    def __init__(self):
        """初始化"""
        self.generated_files = []
    
    def generateProject(self, paths=None):
        """
        生成项目文件
        
        Args:
            paths (dict): 路径字典，包含output等路径
        """
        from src.utils.logger import logger
        from src.core.reverseEngine import global_paths as global_paths_global, global_config
        
        # 使用传入的paths或全局global_paths
        current_paths = paths if paths is not None else global_paths_global
        
        logger().debug("开始生成项目文件...")
        
        # 创建项目结构
        self._createProjectStructure(current_paths)
        
        # 生成project.json
        self._generateProjectJson(current_paths)
        
        # 生成assets目录下的资源
        self._generateAssets()
        
        # 生成meta文件
        if global_config.get('output', {}).get('createMeta', True):
            self._generateMetaFiles(current_paths)
        
        logger().debug(f"项目生成完成，共生成 {len(self.generated_files)} 个文件")
    
    def _createProjectStructure(self, paths):
        """
        创建项目结构
        
        Args:
            paths (dict): 路径字典
        """
        # 创建主要目录结构
        directories = [
            os.path.join(paths.get('output', ''), 'assets'),
            os.path.join(paths.get('output', ''), 'settings'),
            os.path.join(paths.get('output', ''), 'library'),
            os.path.join(paths.get('output', ''), 'temp'),
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def _generateProjectJson(self, paths):
        """
        生成project.json文件
        
        Args:
            paths (dict): 路径字典
        """
        from src.utils.fileManager import fileManager
        from src.utils.logger import logger
        
        # 生成project.json内容
        project_json = {
            "creator": "1.0.0",
            "engine": "cocos-creator",
            "version": "1.0.0",
            "settings": {
                "import": {
                    "polyfills": False
                }
            }
        }
        
        # 写入文件
        output_path = os.path.join(paths.get('output', ''), 'project.json')
        logger().debug(f"写入project.json文件到: {output_path}")
        fileManager.writeFile(output_path, json.dumps(project_json, indent=2, ensure_ascii=False))
        
        # 检查文件是否存在
        if os.path.exists(output_path):
            logger().debug(f"project.json文件已成功创建，大小: {os.path.getsize(output_path)} 字节")
        else:
            logger().error(f"project.json文件创建失败，路径: {output_path}")
        
        self.generated_files.append(output_path)
    
    def _generateAssets(self):
        """
        生成assets目录下的资源
        """
        from src.utils.logger import logger
        logger().debug("生成assets目录下的资源...")
        
        # 这里可以添加更多资源生成逻辑
        # 目前资源已经在resourceProcessor中处理
    
    def _generateMetaFiles(self, paths):
        """
        生成meta文件
        
        Args:
            paths (dict): 路径字典
        """
        from src.utils.logger import logger
        from src.utils.fileManager import fileManager
        
        logger().debug("生成meta文件...")
        
        # 遍历assets目录，为每个文件生成meta文件
        assets_path = os.path.join(paths.get('output', ''), 'assets')
        if os.path.exists(assets_path):
            for root, _, files in os.walk(assets_path):
                for file in files:
                    if not file.endswith('.meta'):  # 跳过已存在的meta文件
                        file_path = os.path.join(root, file)
                        meta_path = file_path + '.meta'
                        self._generateSingleMetaFile(file_path, meta_path)
    
    def _generateSingleMetaFile(self, file_path, meta_path):
        """
        生成单个文件的meta文件
        
        Args:
            file_path (str): 资源文件路径
            meta_path (str): meta文件路径
        """
        from src.utils.fileManager import fileManager
        import uuid
        
        # 生成meta文件内容
        meta_content = {
            "ver": "1.0.3",
            "uuid": str(uuid.uuid4()),
            "asyncLoadAssets": False,
            "subMetas": {}
        }
        
        # 写入文件
        fileManager.writeFile(meta_path, json.dumps(meta_content, indent=2, ensure_ascii=False))
        self.generated_files.append(meta_path)
    
    def getGeneratedFiles(self):
        """
        获取已生成的文件列表
        
        Returns:
            list: 已生成的文件列表
        """
        return self.generated_files

# 创建全局实例
projectGenerator = ProjectGenerator()
