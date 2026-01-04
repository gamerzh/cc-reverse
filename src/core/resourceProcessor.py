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
    
    def processResources(self, paths=None):
        """
        处理资源
        
        Args:
            paths (dict): 路径字典，包含source、res、output等路径
        """
        from src.utils.logger import logger
        import os
        import json
        
        logger().info("开始处理资源...")
        
        if not paths:
            logger().warn("未提供路径信息，无法处理资源")
            return
        
        logger().debug(f"资源处理: paths={paths}")
        
        # 尝试多种资源目录位置，包括编译后的资源结构
        asset_paths = [
            paths.get('res', ''),  # 默认检测到的资源路径
            os.path.join(paths.get('source', ''), 'assets'),  # 直接在项目根目录下的assets
            os.path.join(paths.get('source', ''), 'res'),  # 直接在项目根目录下的res
            os.path.join(paths.get('source', ''), 'src', 'assets'),  # src目录下的assets
            os.path.join(paths.get('source', ''), 'src', 'res')  # src目录下的res
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
        
        # 查找并处理编译后的资源配置文件
        prefab_info = {}
        for valid_asset_path in valid_asset_paths:
            # 查找config.json文件（编译后的资源配置）
            config_files = []
            for root, _, files in os.walk(valid_asset_path):
                for file in files:
                    if file.startswith('config.') and file.endswith('.json'):
                        config_file_path = os.path.join(root, file)
                        config_files.append(config_file_path)
            
            # 处理每个config.json文件
            for config_file_path in config_files:
                try:
                    logger().info(f"处理资源配置文件: {config_file_path}")
                    with open(config_file_path, 'r', encoding='utf-8') as f:
                        config_content = json.load(f)
                    
                    # 解析资源类型映射
                    types = config_content.get('types', [])
                    paths_dict = config_content.get('paths', {})
                    uuids = config_content.get('uuids', [])
                    
                    # 查找Prefab类型索引
                    prefab_type_index = None
                    for i, type_name in enumerate(types):
                        if type_name == 'cc.Prefab':
                            prefab_type_index = i
                            break
                    
                    if prefab_type_index is not None:
                        logger().info(f"找到Prefab类型索引: {prefab_type_index}")
                        
                        # 收集所有Prefab资源
                        for path_id, path_info in paths_dict.items():
                            if isinstance(path_info, list) and len(path_info) > 0 and path_info[1] == prefab_type_index:
                                prefab_path = path_info[0]
                                prefab_info[prefab_path] = {
                                    'path_id': path_id,
                                    'uuid': uuids[int(path_id)] if len(uuids) > int(path_id) else '',
                                    'path': prefab_path
                                }
                            
                except Exception as e:
                    logger().error(f"处理资源配置文件 {config_file_path} 失败: {e}")
        
        # 处理每个资源目录
        for valid_asset_path in valid_asset_paths:
            # 遍历资源目录
            for root, _, files in os.walk(valid_asset_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # 计算相对于资源目录的路径
                    rel_path = os.path.relpath(file_path, valid_asset_path)
                    
                    # 处理不同类型的资源
                    self._processResource(file_path, rel_path, valid_asset_path, paths)
        
        # 处理Prefab资源，将编译后的JSON转换为.prefab格式
        if prefab_info:
            logger().info(f"找到 {len(prefab_info)} 个Prefab资源，开始转换为.prefab格式")
            self._convertCompiledPrefabsToPrefab(prefab_info, paths)
        
        logger().info(f"资源处理完成，共处理 {len(self.processed_resources)} 个资源")
    
    def _processResource(self, file_path, rel_path, asset_root, paths=None):
        """
        处理单个资源
        
        Args:
            file_path (str): 资源文件路径
            rel_path (str): 资源相对路径
            asset_root (str): 资源根目录
            paths (dict): 路径字典，包含output等路径
        """
        from src.utils.logger import logger
        from src.utils.fileManager import fileManager
        
        # 检测文件类型
        kind = filetype.guess(file_path)
        mime_type = kind.mime if kind else 'unknown'
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # 确定资源类型类别
        resource_category = self._determineResourceCategory(mime_type, file_ext)
        
        logger().debug(f"处理资源: {rel_path}, 类型: {mime_type}, 类别: {resource_category}")
        
        # 资源输出路径
        output_path = os.path.join(paths.get('output', ''), 'assets', rel_path)
        
        # 检查是否为编译后的资源配置文件，如果是则跳过，因为会在专门的逻辑中处理
        if rel_path.startswith('config.') and rel_path.endswith('.json'):
            logger().debug(f"跳过资源配置文件: {rel_path}")
            return
        
        try:
            # 根据资源类型进行专门处理
            if resource_category == 'image':
                self._processImageResource(file_path, output_path)
            elif resource_category == 'audio':
                self._processAudioResource(file_path, output_path)
            elif resource_category == 'font':
                self._processFontResource(file_path, output_path)
            elif resource_category in ['json', 'text', 'xml']:
                # 检查是否为可能的Prefab文件（UUID格式的文件名）
                is_prefab_json = False
                if file_ext == '.json':
                    # 获取文件名（不含扩展名）
                    base_name = os.path.splitext(os.path.basename(file_path))[0]
                    # 检查文件名是否符合UUID格式（包含连字符）
                    if '-' in base_name and len(base_name) >= 36:
                        is_prefab_json = True
                        logger().debug(f"跳过可能的Prefab JSON文件，将由专门的处理逻辑处理: {rel_path}")
                
                # 如果不是Prefab JSON文件，则正常处理
                if not is_prefab_json:
                    self._processTextResource(file_path, output_path)
            elif resource_category == 'prefab':
                self._processPrefabResource(file_path, output_path)
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
            '.txt': 'text',
            '.prefab': 'prefab'  # 添加Prefab文件类型支持
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
        import json
        
        # 确保目录存在
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # 读取并复制文本文件
        content = fileManager.readFile(source_path)
        
        # 检查是否为编译后的Prefab JSON文件
        if target_path.endswith('.json'):
            try:
                # 尝试解析JSON
                json_content = json.loads(content)
                
                # 检查是否为编译后的资源格式
                if isinstance(json_content, list) and len(json_content) > 0:
                    # 检查是否包含Prefab相关内容
                    # 编译后的Prefab文件结构比较特殊，我们需要进一步分析
                    # 这里先实现基本的转换逻辑，将符合条件的JSON转换为.prefab
                    
                    # 获取文件名（不含扩展名）
                    base_name = os.path.splitext(os.path.basename(target_path))[0]
                    # 检查文件名是否符合UUID格式
                    if '-' in base_name:
                        # 假设这是一个Prefab文件，将其扩展名改为.prefab
                        prefab_target_path = target_path.replace('.json', '.prefab')
                        logger().info(f"将编译后的JSON文件转换为Prefab: {os.path.basename(target_path)} -> {os.path.basename(prefab_target_path)}")
                        
                        # 这里可以添加更复杂的解析逻辑，将编译后的格式转换为原始Prefab格式
                        # 目前先简单复制文件，后续可以完善解析逻辑
                        fileManager.writeFile(prefab_target_path, content)
                        return
            except json.JSONDecodeError:
                pass
            except Exception as e:
                logger().error(f"处理JSON文件时出错: {e}")
        
        # 普通文本文件直接复制
        fileManager.writeFile(target_path, content)
    
    def _processPrefabResource(self, source_path, target_path):
        """
        处理Prefab资源
        
        Args:
            source_path (str): 源文件路径
            target_path (str): 目标文件路径
        """
        from src.utils.fileManager import fileManager
        # 确保目录存在
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # 直接复制prefab文件
        fileManager.copyFile(source_path, target_path)
    
    def _convertCompiledPrefabsToPrefab(self, prefab_info, paths):
        """
        将编译后的Prefab资源转换为.prefab格式
        
        Args:
            prefab_info (dict): Prefab资源信息字典
            paths (dict): 路径字典
        """
        from src.utils.fileManager import fileManager
        from src.utils.logger import logger
        import os
        import json
        import uuid as uuid_module
        
        logger().info("开始转换编译后的Prefab资源...")
        
        source_res_path = paths.get('res', '')
        output_assets_path = os.path.join(paths.get('output', ''), 'assets')
        
        # 遍历所有Prefab资源
        for prefab_path, info in prefab_info.items():
            try:
                # 构建编译后的资源文件路径（可能是带UUID的JSON文件）
                # 尝试多种可能的路径格式
                possible_source_paths = [
                    # 直接使用路径
                    os.path.join(source_res_path, prefab_path),
                    # 带.json扩展名
                    os.path.join(source_res_path, prefab_path + '.json'),
                    # 在assets目录下
                    os.path.join(source_res_path, 'assets', prefab_path),
                    # 在assets目录下，带.json扩展名
                    os.path.join(source_res_path, 'assets', prefab_path + '.json'),
                    # 在res目录下
                    os.path.join(source_res_path, 'res', prefab_path),
                    # 在res目录下，带.json扩展名
                    os.path.join(source_res_path, 'res', prefab_path + '.json')
                ]
                
                # 查找实际存在的文件
                actual_source_path = None
                for path in possible_source_paths:
                    if os.path.exists(path):
                        actual_source_path = path
                        break
                
                # 如果找到源文件，读取其内容
                prefab_content = None
                if actual_source_path and os.path.isfile(actual_source_path):
                    logger().info(f"读取编译后的Prefab资源: {actual_source_path}")
                    try:
                        with open(actual_source_path, 'r', encoding='utf-8') as f:
                            prefab_content = json.load(f)
                    except Exception as e:
                        logger().warn(f"读取Prefab资源 {actual_source_path} 失败，使用默认结构: {e}")
                
                # 创建Prefab文件路径
                prefab_file_path = os.path.join(output_assets_path, prefab_path + '.prefab')
                
                # 确保目录存在
                os.makedirs(os.path.dirname(prefab_file_path), exist_ok=True)
                
                # 如果没有读取到内容，使用默认结构
                if prefab_content is None:
                    # 创建基本的Prefab文件结构
                    prefab_content = [
                        {
                            "__type__": "cc.Prefab",
                            "_name": "",
                            "_objFlags": 0,
                            "_native": "",
                            "data": {
                                "__id__": 1
                            },
                            "optimizationPolicy": 0,
                            "asyncLoadAssets": False,
                            "readonly": False
                        },
                        {
                            "__type__": "cc.Node",
                            "_name": prefab_path.split('/')[-1],
                            "_objFlags": 0,
                            "_parent": None,
                            "_children": [],
                            "_active": True,
                            "_components": [],
                            "_prefab": {
                                "__id__": 2
                            },
                            "_opacity": 255,
                            "_color": {
                                "__type__": "cc.Color",
                                "r": 255,
                                "g": 255,
                                "b": 255,
                                "a": 255
                            },
                            "_contentSize": {
                                "__type__": "cc.Size",
                                "width": 100,
                                "height": 100
                            },
                            "_anchorPoint": {
                                "__type__": "cc.Vec2",
                                "x": 0.5,
                                "y": 0.5
                            },
                            "_trs": {
                                "__type__": "TypedArray",
                                "ctor": "Float64Array",
                                "array": [0, 0, 0, 0, 0, 0, 1, 1, 1, 1]
                            },
                            "_eulerAngles": {
                                "__type__": "cc.Vec3",
                                "x": 0,
                                "y": 0,
                                "z": 0
                            },
                            "_skewX": 0,
                            "_skewY": 0,
                            "_is3DNode": False,
                            "_groupIndex": 0,
                            "groupIndex": 0,
                            "_id": ""
                        },
                        {
                            "__type__": "cc.PrefabInfo",
                            "root": {
                                "__id__": 1
                            },
                            "asset": {
                                "__id__": 0
                            },
                            "fileId": "",
                            "sync": False
                        }
                    ]
                
                # 写入Prefab文件
                fileManager.writeFile(prefab_file_path, json.dumps(prefab_content, indent=2, ensure_ascii=False))
                logger().info(f"生成Prefab文件: {prefab_file_path}")
                
                # 生成meta文件
                meta_file_path = prefab_file_path + '.meta'
                meta_content = {
                    "ver": "1.0.3",
                    "uuid": info.get('uuid', str(uuid_module.uuid4())),
                    "asyncLoadAssets": False,
                    "subMetas": {}
                }
                fileManager.writeFile(meta_file_path, json.dumps(meta_content, indent=2, ensure_ascii=False))
                logger().info(f"生成Prefab.meta文件: {meta_file_path}")
                
                # 添加到已处理资源列表
                self.processed_resources.append({
                    'source': actual_source_path or '',
                    'target': prefab_file_path,
                    'type': 'application/json',
                    'category': 'prefab',
                    'relative_path': prefab_path + '.prefab',
                    'file_ext': '.prefab'
                })
                
            except Exception as e:
                logger().error(f"转换Prefab资源 {prefab_path} 失败: {e}")
    
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
