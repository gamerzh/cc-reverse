#!/usr/bin/env python3
"""
资源处理器
"""

import os
import json
import shutil

# 本地实现logger函数，避免依赖外部模块
def logger():
    """日志函数，返回日志方法字典"""
    def info(msg, **kwargs):
        print(f"[INFO] {msg}")
    
    def success(msg, **kwargs):
        print(f"[SUCCESS] {msg}")
    
    def warn(msg, **kwargs):
        print(f"[WARN] {msg}")
    
    def error(msg, **kwargs):
        print(f"[ERROR] {msg}")
    
    def debug(msg, **kwargs):
        print(f"[DEBUG] {msg}")
    
    def exception(msg, e, **kwargs):
        print(f"[EXCEPTION] {msg}: {e}")
    
    def set_level(level):
        pass
    
    def set_verbose(verbose):
        pass
    
    return {
        "info": info,
        "success": success,
        "warn": warn,
        "error": error,
        "debug": debug,
        "exception": exception,
        "set_level": set_level,
        "set_verbose": set_verbose
    }

# 本地实现FileManager类，避免依赖外部模块
class FileManager:
    """文件管理器类，实现常用的文件操作"""
    
    def readFile(self, file_path):
        """读取文件内容"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def writeFile(self, file_path, content):
        """写入文件内容"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def copyFile(self, source_path, target_path):
        """复制文件"""
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        shutil.copy2(source_path, target_path)
    
    def deleteDirectoriesByName(self, directory, names):
        """删除指定名称的目录"""
        for name in names:
            dir_path = os.path.join(directory, name)
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path, ignore_errors=True)
                logger()['info'](f"删除目录: {dir_path}")
    
    def deleteEmptyDirectories(self, directory):
        """删除空目录"""
        for root, dirs, files in os.walk(directory, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    logger()['debug'](f"删除空目录: {dir_path}")

# 创建全局实例
fileManager = FileManager()

class ResourceProcessor:
    """
    资源处理器类
    """
    
    def __init__(self):
        """初始化"""
        self.assets = []
        self.prefabs = []
        self.scenes = []
        self.textures = []
    
    def processResources(self, paths=None):
        """
        处理资源文件
        
        Args:
            paths (dict): 路径字典
        """
        import shutil
        
        logger()['info']("开始处理资源...")
        
        if not paths:
            logger()['warn']("未提供路径信息，无法处理资源")
            return
        
        logger()['debug'](f"资源处理: paths={paths}")
        
        # 尝试多种资源位置目录，包括编译后的资源结构
        asset_path_candidates = [
            paths.get('res', ''),  # 编译后的res目录
            os.path.join(paths.get('source', ''), 'res'),  # 源代码res目录
            os.path.join(paths.get('source', ''), 'assets'),  # Cocos Creator assets目录
            paths.get('assets', '')  # 直接提供的assets目录
        ]
        
        # 过滤出存在的资源目录
        valid_asset_paths = []
        for path in asset_path_candidates:
            if path and os.path.exists(path):
                valid_asset_paths.append(path)
                logger()['info'](f"找到资源目录: {path}")
        
        if not valid_asset_paths:
            logger()['warn']("未找到资源目录")
            return
        
        # 处理配置文件，查找资源映射
        config_dirs = []
        for asset_path in valid_asset_paths:
            config_dir = os.path.dirname(asset_path)
            if os.path.exists(config_dir):
                config_dirs.append(config_dir)
        
        # 查找并处理资源配置文件
        prefab_type_index = None
        scene_type_index = None
        paths_dict = {}
        
        for config_dir in config_dirs:
            config_files = []
            # 查找所有可能的配置文件
            for root, dirs, files in os.walk(config_dir):
                for file in files:
                    if file.endswith('.json') or file.endswith('.js'):
                        config_files.append(os.path.join(root, file))
            
            for config_file_path in config_files:
                try:
                    logger()['info'](f"处理资源配置文件: {config_file_path}")
                    with open(config_file_path, 'r', encoding='utf-8') as f:
                        config_content = json.load(f)
                    
                    # 查找资源映射和类型索引
                    if isinstance(config_content, dict):
                        if 'paths' in config_content:
                            paths_dict.update(config_content['paths'])
                        if 'types' in config_content:
                            for idx, type_info in enumerate(config_content['types']):
                                if isinstance(type_info, str):
                                    if 'prefab' in type_info.lower():
                                        prefab_type_index = idx
                                    elif 'scene' in type_info.lower():
                                        scene_type_index = idx
                    
                    if prefab_type_index is not None:
                        logger()['info'](f"找到Prefab类型索引: {prefab_type_index}")
                        logger()['info'](f"Config文件目录: {config_dir}")
                        
                        # 收集所有Prefab资源
                        self._collectPrefabResources(config_content, config_dir, paths_dict)
                    
                    if scene_type_index is not None:
                        logger()['info'](f"找到Scene类型索引: {scene_type_index}")
                        logger()['info'](f"Config文件目录: {config_dir}")
                        
                        # 收集所有Scene资源
                        self._collectSceneResources(config_content, config_dir, paths_dict)
                    
                    # 收集所有资源的路径映射
                    logger()['info'](f"开始收集资源路径映射，Config目录: {config_dir}")
                    for path_id, path_info in paths_dict.items():
                        if isinstance(path_info, list) and len(path_info) > 0:
                            resource_rel_path = path_info[0]
                            if resource_rel_path.startswith('textures/'):
                                # 图片资源
                                resource_map = {
                                    'path_id': path_id,
                                    'resource_rel_path': resource_rel_path,
                                    'type': 'texture',
                                    'config_dir': config_dir
                                }
                                logger()['debug'](f"收集图片资源映射: {path_id} -> {resource_rel_path}")
                                
                                # 添加到需要创建的图片路径列表
                                full_path = os.path.join(paths.get('output', ''), 'assets', resource_rel_path[:-4])
                                self.textures.append({
                                    'path': full_path + '.png',
                                    'resource_map': resource_map,
                                    'original_path': resource_rel_path
                                })
                                logger()['debug'](f"添加图片路径到创建列表: {full_path}.png")
                            elif resource_rel_path.startswith('fonts/'):
                                # 字体资源
                                resource_map = {
                                    'path_id': path_id,
                                    'resource_rel_path': resource_rel_path,
                                    'type': 'font',
                                    'config_dir': config_dir
                                }
                                logger()['debug'](f"收集字体资源映射: {path_id} -> {resource_rel_path}")
                                
                                # 添加到需要创建的字体路径列表
                                full_path = os.path.join(paths.get('output', ''), 'assets', resource_rel_path)
                                self.assets.append({
                                    'path': full_path,
                                    'resource_map': resource_map,
                                    'original_path': resource_rel_path
                                })
                                logger()['debug'](f"添加字体路径到创建列表: {full_path}")
                            elif resource_rel_path.startswith('sound/'):
                                # 音效资源
                                resource_map = {
                                    'path_id': path_id,
                                    'resource_rel_path': resource_rel_path,
                                    'type': 'sound',
                                    'config_dir': config_dir
                                }
                                logger()['debug'](f"收集音效资源映射: {path_id} -> {resource_rel_path}")
                                
                                # 添加到需要创建的音效路径列表
                                full_path = os.path.join(paths.get('output', ''), 'assets', resource_rel_path[:-4])
                                self.assets.append({
                                    'path': full_path + '.mp3',
                                    'resource_map': resource_map,
                                    'original_path': resource_rel_path
                                })
                                logger()['debug'](f"添加音效路径到创建列表: {full_path}.mp3")
                            elif resource_rel_path.startswith('spine/'):
                                # 骨骼动画资源
                                resource_map = {
                                    'path_id': path_id,
                                    'resource_rel_path': resource_rel_path,
                                    'type': 'spine',
                                    'config_dir': config_dir
                                }
                                logger()['debug'](f"收集骨骼动画资源映射: {path_id} -> {resource_rel_path}")
                                
                                # 添加到需要创建的骨骼动画路径列表
                                full_path = os.path.join(paths.get('output', ''), 'assets', resource_rel_path)
                                self.assets.append({
                                    'path': full_path,
                                    'resource_map': resource_map,
                                    'original_path': resource_rel_path
                                })
                                logger()['debug'](f"添加骨骼动画路径到创建列表: {full_path}")
                except Exception as e:
                    logger()['exception'](f"处理配置文件失败: {config_file_path}", e)
                    continue
        
        # 处理资源文件
        self._processResourceFiles(valid_asset_paths, paths)
        
        # 生成资源配置文件
        self._generateResourceConfigs(paths)
        
        logger()['success']("资源处理完成")
    
    def _collectPrefabResources(self, config_content, config_dir, paths_dict):
        """
        收集Prefab资源
        
        Args:
            config_content (dict): 配置文件内容
            config_dir (str): 配置文件目录
            paths_dict (dict): 资源路径字典
        """
        logger()['debug']("开始收集Prefab资源")
        
        # 查找prefabs数组
        if 'prefabs' in config_content:
            for prefab_info in config_content['prefabs']:
                if isinstance(prefab_info, dict):
                    self.prefabs.append({
                        'info': prefab_info,
                        'config_dir': config_dir
                    })
                    logger()['debug'](f"收集Prefab资源: {prefab_info.get('path', 'unknown')}")
        
        logger()['debug'](f"共收集到 {len(self.prefabs)} 个Prefab资源")
    
    def _collectSceneResources(self, config_content, config_dir, paths_dict):
        """
        收集Scene资源
        
        Args:
            config_content (dict): 配置文件内容
            config_dir (str): 配置文件目录
            paths_dict (dict): 资源路径字典
        """
        logger()['debug']("开始收集Scene资源")
        
        # 查找scenes数组
        if 'scenes' in config_content:
            for scene_info in config_content['scenes']:
                if isinstance(scene_info, dict):
                    self.scenes.append({
                        'info': scene_info,
                        'config_dir': config_dir
                    })
                    logger()['debug'](f"收集Scene资源: {scene_info.get('path', 'unknown')}")
        
        logger()['debug'](f"共收集到 {len(self.scenes)} 个Scene资源")
    
    def _processResourceFiles(self, asset_paths, paths):
        """
        处理资源文件
        
        Args:
            asset_paths (list): 资源目录列表
            paths (dict): 路径字典
        """
        logger()['info']("开始处理资源文件")
        
        output_assets_dir = os.path.join(paths.get('output', ''), 'assets')
        
        # 确保输出目录存在
        os.makedirs(output_assets_dir, exist_ok=True)
        
        # 复制资源文件到输出目录
        for asset_path in asset_paths:
            try:
                logger()['info'](f"复制资源文件从: {asset_path} 到: {output_assets_dir}")
                
                # 使用shutil.copytree复制整个资源目录
                # 注意：如果目标目录已存在，copytree会失败，所以需要处理这种情况
                for root, dirs, files in os.walk(asset_path):
                    for file in files:
                        source_file = os.path.join(root, file)
                        rel_path = os.path.relpath(source_file, asset_path)
                        target_file = os.path.join(output_assets_dir, rel_path)
                        
                        # 确保目标目录存在
                        os.makedirs(os.path.dirname(target_file), exist_ok=True)
                        
                        # 复制文件
                        shutil.copy2(source_file, target_file)
                        logger()['debug'](f"复制资源文件: {rel_path}")
            except Exception as e:
                logger()['exception'](f"复制资源文件失败: {asset_path}", e)
                continue
    
    def _generateResourceConfigs(self, paths):
        """
        生成资源配置文件
        
        Args:
            paths (dict): 路径字典
        """
        logger()['info']("开始生成资源配置文件")
        
        output_dir = paths.get('output', '')
        
        # 生成资源映射配置
        resource_map_config = {
            'textures': self.textures,
            'assets': self.assets,
            'prefabs': self.prefabs,
            'scenes': self.scenes
        }
        
        resource_map_path = os.path.join(output_dir, 'resource_map.json')
        try:
            with open(resource_map_path, 'w', encoding='utf-8') as f:
                json.dump(resource_map_config, f, indent=2, ensure_ascii=False)
            logger()['success'](f"生成资源映射配置文件: {resource_map_path}")
        except Exception as e:
            logger()['exception'](f"生成资源映射配置文件失败", e)
    
    def getAssets(self):
        """
        获取处理后的资源列表
        
        Returns:
            list: 资源列表
        """
        return self.assets
    
    def getPrefabs(self):
        """
        获取处理后的Prefab列表
        
        Returns:
            list: Prefab列表
        """
        return self.prefabs
    
    def getScenes(self):
        """
        获取处理后的Scene列表
        
        Returns:
            list: Scene列表
        """
        return self.scenes
    
    def getResourceStats(self):
        """
        获取资源统计信息
        
        Returns:
            dict: 资源统计信息，包含total等字段
        """
        total = len(self.assets) + len(self.prefabs) + len(self.scenes) + len(self.textures)
        return {
            'total': total,
            'assets': len(self.assets),
            'prefabs': len(self.prefabs),
            'scenes': len(self.scenes),
            'textures': len(self.textures)
        }
    
    def convertCompiledScene(self, scene_info, paths):
        """
        将编译后的场景资源转换为.fire格式
        Args:
            scene_info (dict): 场景资源信息字典
            paths (dict): 路径字典
        """
        from utils.fileManager import fileManager
        import os
        import json
        import uuid as uuid_module
        
        logger()['info']("开始转换编译后的Scene资源...")
        
        source_res_path = paths.get('res', '')
        output_assets_path = os.path.join(paths.get('output', ''), 'assets')
        
        # 遍历所有场景资源
        for scene_path, info in scene_info.items():
            try:
                logger()['info'](f"处理场景: {scene_path}")
                
                # 创建输出目录结构
                scene_output_dir = os.path.join(output_assets_path, 'scenes')
                os.makedirs(scene_output_dir, exist_ok=True)
                
                # 生成.fire场景文件
                scene_file_path = os.path.join(scene_output_dir, os.path.basename(scene_path) + '.fire')
                
                # 创建基本场景结构
                scene_data = {
                    "ccType": "cc.SceneAsset",
                    "_name": os.path.basename(scene_path),
                    "_objFlags": 0,
                    "_native": "",
                    "_uuid": str(uuid_module.uuid4()),
                    "_id": 0,
                    "_scene": {
                        "ccType": "cc.Scene",
                        "_name": os.path.basename(scene_path),
                        "_objFlags": 0,
                        "_components": [],
                        "_persistRootNode": None,
                        "gravity": [0, -320],
                        "name": os.path.basename(scene_path),
                        "autoReleaseAssets": True,
                        "_physicsManager": {
                            "enable": False,
                            "debugDrawFlags": 0,
                            "gravity": [0, -320]
                        },
                        "_collisionManager": {
                            "enable": False,
                            "enableDebugDraw": False,
                            "enableDrawBoundingBox": False
                        },
                        "_physics3DManager": {
                            "enable": False,
                            "autoSimulation": True
                        },
                        "_renderSettings": {
                            "defaultSkybox": None,
                            "ambient": [0.2, 0.2, 0.2, 1.0],
                            "fog": {
                                "enabled": False,
                                "color": [0.8, 0.8, 0.8, 1.0],
                                "near": 0.01,
                                "far": 1000.0,
                                "density": 0.001,
                                "mode": 1
                            },
                            "shadows": {
                                "enabled": False,
                                "type": 0,
                                "distance": 1000.0,
                                "bias": 0.05,
                                "normalBias": 0.4,
                                "mapSize": 1024
                            },
                            "mainLight": {
                                "useMainLight": True,
                                "direction": [-0.5, -0.5, -1.0],
                                "intensity": 0.7,
                                "color": [1.0, 1.0, 1.0, 1.0]
                            }
                        },
                        "_cameraSettings": {
                            "defaultClearColor": [0.2, 0.3, 0.4, 1.0],
                            "defaultClearFlags": 15,
                            "defaultCamera": None
                        }
                    }
                }
                
                # 写入场景文件
                fileManager.writeFile(scene_file_path, json.dumps(scene_data, indent=2))
                logger()['success'](f"生成场景文件: {scene_file_path}")
            except Exception as e:
                logger()['exception'](f"转换场景资源失败: {scene_path}", e)
    
    def convertCompiledPrefab(self, prefab_info, paths):
        """
        将编译后的预制体资源转换为.prefab格式
        
        Args:
            prefab_info (dict): 预制体资源信息字典
            paths (dict): 路径字典
        """
        from utils.fileManager import fileManager
        import os
        import json
        import uuid as uuid_module
        
        logger()['info']("开始转换编译后的Prefab资源...")
        
        source_res_path = paths.get('res', '')
        output_assets_path = os.path.join(paths.get('output', ''), 'assets')
        
        # 遍历所有预制体资源
        for prefab_path, info in prefab_info.items():
            try:
                logger()['info'](f"处理预制体: {prefab_path}")
                
                # 创建输出目录结构
                prefab_output_dir = os.path.join(output_assets_path, 'prefabs')
                os.makedirs(prefab_output_dir, exist_ok=True)
                
                # 生成.prefab文件
                prefab_file_path = os.path.join(prefab_output_dir, os.path.basename(prefab_path) + '.prefab')
                
                # 创建基本预制体结构
                prefab_data = {
                    "ccType": "cc.PrefabAsset",
                    "_name": os.path.basename(prefab_path),
                    "_objFlags": 0,
                    "_native": "",
                    "_uuid": str(uuid_module.uuid4()),
                    "_id": 0,
                    "data": {
                        "ccType": "cc.Node",
                        "_name": os.path.basename(prefab_path),
                        "_objFlags": 0,
                        "_components": [],
                        "active": True,
                        "_persistNode": False,
                        "_position": [0, 0, 0],
                        "_rotation": [0, 0, 0, 1],
                        "_scale": [1, 1, 1],
                        "_eulerAngles": [0, 0, 0],
                        "_anchorPoint": [0.5, 0.5],
                        "_skew": [0, 0],
                        "_contentSize": [100, 100],
                        "_color": [255, 255, 255, 255],
                        "_opacity": 255,
                        "_parent": None,
                        "_children": []
                    },
                    "asyncLoadAssets": False,
                    "optimizeBatchInEditor": True
                }
                
                # 写入预制体文件
                fileManager.writeFile(prefab_file_path, json.dumps(prefab_data, indent=2))
                logger()['success'](f"生成预制体文件: {prefab_file_path}")
            except Exception as e:
                logger()['exception'](f"转换预制体资源失败: {prefab_path}", e)
    
    def extractAllResources(self, paths):
        """
        提取所有资源
        
        Args:
            paths (dict): 路径字典
        """
        import os
        import shutil
        
        logger()['info']("开始提取所有资源...")
        
        output_assets_dir = os.path.join(paths.get('output', ''), 'assets')
        source_dir = paths.get('source', '')
        
        # 确保输出目录存在
        os.makedirs(output_assets_dir, exist_ok=True)
        
        # 提取资源文件
        resource_extensions = [
            '.png', '.jpg', '.jpeg', '.gif', '.webp',  # 图片资源
            '.mp3', '.wav', '.ogg', '.flac',  # 音频资源
            '.mp4', '.mov', '.webm',  # 视频资源
            '.json', '.xml',  # 配置资源
            '.font', '.ttf', '.otf',  # 字体资源
            '.atlas',  # 图集资源
            '.anim',  # 动画资源
            '.fire',  # 场景资源
            '.prefab',  # 预制体资源
            '.csd',  # Cocos Studio资源
            '.csb',  # 二进制Cocos Studio资源
            '.dragonbones', '.dbbin',  # DragonBones动画资源
            '.skel', '.atlas',  # Spine动画资源
            '.lua'  # Lua脚本
        ]
        
        # 遍历源目录，查找所有资源文件
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if any(file.endswith(ext) for ext in resource_extensions):
                    source_file = os.path.join(root, file)
                    rel_path = os.path.relpath(source_file, source_dir)
                    target_file = os.path.join(output_assets_dir, rel_path)
                    
                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(target_file), exist_ok=True)
                    
                    try:
                        # 复制资源文件
                        shutil.copy2(source_file, target_file)
                        logger()['debug'](f"提取资源文件: {rel_path}")
                    except Exception as e:
                        logger()['exception'](f"复制资源文件失败: {source_file}", e)
                        continue
        
        logger()['success']("资源提取完成")

# 创建全局实例
resourceProcessor = ResourceProcessor()