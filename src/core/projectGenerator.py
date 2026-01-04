#!/usr/bin/env python3
"""
项目生成器
"""

import os
import json
import uuid

class ProjectGenerator:
    """项目生成器类"""
    
    def __init__(self):
        """初始化"""
        self.generated_files = []
        self.asset_uuid_map = {}  # 存储资产UUID映射
    
    def generateProject(self, paths=None):
        """
        生成项目文件
        
        Args:
            paths (dict): 路径字典，包含output等路径
        """
        from src.utils.logger import logger
        from src.core.reverseEngine import global_paths as global_paths_global, global_config, global_cocosVersion
        
        # 使用传入的paths或全局global_paths
        current_paths = paths if paths is not None else global_paths_global
        
        logger().info("开始生成项目文件...")
        
        # 创建项目结构
        self._createProjectStructure(current_paths)
        
        # 生成project.json
        self._generateProjectJson(current_paths, global_cocosVersion)
        
        # 生成settings目录下的配置文件
        self._generateSettingsFiles(current_paths)
        
        # 生成package.json（如果需要）
        self._generatePackageJson(current_paths)
        
        # 生成assets目录下的资源
        self._generateAssets()
        
        # 生成meta文件
        if global_config.get('output', {}).get('createMeta', True):
            self._generateMetaFiles(current_paths)
        
        # 生成场景文件
        self._generateDefaultScene(current_paths)
        
        logger().info(f"项目生成完成，共生成 {len(self.generated_files)} 个文件")
    
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
            os.path.join(paths.get('output', ''), 'assets', 'scripts'),
            os.path.join(paths.get('output', ''), 'assets', 'resources'),
            os.path.join(paths.get('output', ''), 'assets', 'scenes'),
            os.path.join(paths.get('output', ''), 'assets', 'textures'),
            os.path.join(paths.get('output', ''), 'assets', 'audio'),
            os.path.join(paths.get('output', ''), 'assets', 'fonts')
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def _generateProjectJson(self, paths, cocos_version):
        """
        生成project.json文件
        
        Args:
            paths (dict): 路径字典
            cocos_version (str): Cocos Creator版本
        """
        from src.utils.fileManager import fileManager
        from src.utils.logger import logger
        
        # 根据Cocos Creator版本设置不同的配置
        if cocos_version.startswith('2.4'):
            creator_version = "2.4.15"
            engine_version = "cocos2d-js"
        else:  # 2.3.x及以下
            creator_version = "2.3.4"
            engine_version = "cocos2d-js"
        
        # 生成project.json内容
        project_json = {
            "creator": creator_version,
            "engine": engine_version,
            "version": "1.0.0",
            "packageManager": {
                "packageUrl": "https://packages.cocos.com/",
                "backupUrl": "",
                "customSourcePrefix": "",
                "builtin": {},
                "dependencies": {},
                "custom": {}
            },
            "modules": [],
            "settings": {
                "import": {
                    "polyfills": False
                },
                "exportAsModule": True,
                "scripting": {
                    "defaultScriptLanguage": "javascript"
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
    
    def _generateSettingsFiles(self, paths):
        """
        生成settings目录下的配置文件
        
        Args:
            paths (dict): 路径字典
        """
        from src.utils.fileManager import fileManager
        from src.utils.logger import logger
        
        settings_dir = os.path.join(paths.get('output', ''), 'settings')
        
        # 生成editor.json
        editor_json = {
            "defaultScene": "db://assets/scenes/Default.scene",
            "previewWidth": 960,
            "previewHeight": 640,
            "showFPS": True,
            "debugShowFlags": {
                "renderers": 0,
                "collider": False,
                "animation": False
            }
        }
        
        editor_path = os.path.join(settings_dir, 'editor.json')
        fileManager.writeFile(editor_path, json.dumps(editor_json, indent=2, ensure_ascii=False))
        self.generated_files.append(editor_path)
        logger().debug(f"生成editor.json文件: {editor_path}")
        
        # 生成project.json（settings目录下）
        settings_project_json = {
            "project_type": "javascript",
            "debug": {
                "devtool": "source-map"
            },
            "renderPipeline": "builtin-standard"
        }
        
        settings_project_path = os.path.join(settings_dir, 'project.json')
        fileManager.writeFile(settings_project_path, json.dumps(settings_project_json, indent=2, ensure_ascii=False))
        self.generated_files.append(settings_project_path)
        logger().debug(f"生成settings/project.json文件: {settings_project_path}")
    
    def _generatePackageJson(self, paths):
        """
        生成package.json文件
        
        Args:
            paths (dict): 路径字典
        """
        from src.utils.fileManager import fileManager
        from src.utils.logger import logger
        
        package_json = {
            "name": "cc-reverse-project",
            "version": "1.0.0",
            "description": "Cocos Creator reverse engineered project",
            "main": "main.js",
            "scripts": {
                "build": "cocos build",
                "preview": "cocos preview"
            },
            "keywords": ["cocos-creator", "reverse-engineering"],
            "author": "",
            "license": "MIT"
        }
        
        package_path = os.path.join(paths.get('output', ''), 'package.json')
        fileManager.writeFile(package_path, json.dumps(package_json, indent=2, ensure_ascii=False))
        self.generated_files.append(package_path)
        logger().debug(f"生成package.json文件: {package_path}")
    
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
        
        logger().info("生成meta文件...")
        
        # 遍历assets目录，为每个文件生成meta文件
        assets_path = os.path.join(paths.get('output', ''), 'assets')
        if os.path.exists(assets_path):
            # 先为目录生成meta文件
            for root, dirs, files in os.walk(assets_path):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    meta_path = dir_path + '.meta'
                    if not os.path.exists(meta_path):
                        self._generateDirectoryMetaFile(dir_path, meta_path)
            
            # 再为文件生成meta文件
            for root, _, files in os.walk(assets_path):
                for file in files:
                    if not file.endswith('.meta'):  # 跳过已存在的meta文件
                        file_path = os.path.join(root, file)
                        meta_path = file_path + '.meta'
                        if not os.path.exists(meta_path):
                            self._generateSingleMetaFile(file_path, meta_path)
    
    def _generateDirectoryMetaFile(self, dir_path, meta_path):
        """
        生成目录的meta文件
        
        Args:
            dir_path (str): 目录路径
            meta_path (str): meta文件路径
        """
        from src.utils.fileManager import fileManager
        
        # 生成目录meta文件内容
        meta_content = {
            "ver": "1.0.1",
            "uuid": str(uuid.uuid4()),
            "isDir": True,
            "subMetas": {}
        }
        
        # 写入文件
        fileManager.writeFile(meta_path, json.dumps(meta_content, indent=2, ensure_ascii=False))
        self.generated_files.append(meta_path)
    
    def _generateSingleMetaFile(self, file_path, meta_path):
        """
        生成单个文件的meta文件
        
        Args:
            file_path (str): 资源文件路径
            meta_path (str): meta文件路径
        """
        from src.utils.fileManager import fileManager
        import uuid
        
        # 获取文件扩展名
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # 根据文件类型生成不同的meta内容
        meta_content = {
            "ver": "1.0.3",
            "uuid": str(uuid.uuid4()),
            "asyncLoadAssets": False,
            "subMetas": {}
        }
        
        # 根据文件类型添加特定配置
        if file_ext in ['.js', '.ts']:
            meta_content['script'] = {
                "classname": "",
                "super": "cc.Component"
            }
        elif file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
            meta_content['texture'] = {
                "type": 0,
                "aniso": 1,
                "filterMode": 1,
                "wrapMode": 1,
                "genMipmaps": True,
                "premultiplyAlpha": True
            }
        elif file_ext in ['.mp3', '.wav', '.ogg', '.flac']:
            meta_content['audio'] = {
                "loadMode": 0,
                "preload": False
            }
        elif file_ext in ['.scene']:
            meta_content['scene'] = {
                "autoStart": True
            }
        
        # 写入文件
        fileManager.writeFile(meta_path, json.dumps(meta_content, indent=2, ensure_ascii=False))
        self.generated_files.append(meta_path)
        
        # 存储UUID映射，以便其他文件引用
        rel_path = file_path.replace('\\', '/')
        self.asset_uuid_map[rel_path] = meta_content['uuid']
    
    def _generateDefaultScene(self, paths):
        """
        生成默认场景文件
        
        Args:
            paths (dict): 路径字典
        """
        from src.utils.fileManager import fileManager
        from src.utils.logger import logger
        
        # 创建scenes目录
        scenes_dir = os.path.join(paths.get('output', ''), 'assets', 'scenes')
        os.makedirs(scenes_dir, exist_ok=True)
        
        # 生成默认场景内容
        scene_content = {
            "compressionType": 0,
            "content": {
                "__type__": "cc.SceneAsset",
                "scene": {
                    "__id__": 1
                }
            },
            "subMetas": {
                "scene": {
                    "__type__": "cc.Prefab",
                    "data": {
                        "__id__": 2
                    }
                }
            }
        }
        
        # 简化的场景数据
        scene_data = {
            "_name": "Default",
            "_objFlags": 0,
            "_components": [
                {
                    "__type__": "cc.Canvas",
                    "_name": "Canvas",
                    "_objFlags": 0,
                    "node": {
                        "__id__": 3
                    },
                    "designResolution": {
                        "width": 960,
                        "height": 640
                    },
                    "fitWidth": True,
                    "fitHeight": True
                }
            ],
            "_active": True,
            "_children": [
                {
                    "_name": "Canvas",
                    "_objFlags": 0,
                    "_components": [
                        {
                            "__type__": "cc.TransformComponent",
                            "_name": "Transform",
                            "_objFlags": 0,
                            "localPosition": {
                                "x": 0,
                                "y": 0,
                                "z": 0
                            },
                            "localRotation": {
                                "x": 0,
                                "y": 0,
                                "z": 0,
                                "w": 1
                            },
                            "localScale": {
                                "x": 1,
                                "y": 1,
                                "z": 1
                            }
                        },
                        {
                            "__id__": 4
                        }
                    ],
                    "_active": True,
                    "_children": []
                }
            ]
        }
        
        scene_path = os.path.join(scenes_dir, 'Default.scene')
        fileManager.writeFile(scene_path, json.dumps(scene_data, indent=2, ensure_ascii=False))
        self.generated_files.append(scene_path)
        logger().info(f"生成默认场景文件: {scene_path}")
    
    def getGeneratedFiles(self):
        """
        获取已生成的文件列表
        
        Returns:
            list: 已生成的文件列表
        """
        return self.generated_files
    
    def getAssetUUIDMap(self):
        """
        获取资产UUID映射
        
        Returns:
            dict: 资产UUID映射
        """
        return self.asset_uuid_map

# 创建全局实例
projectGenerator = ProjectGenerator()
