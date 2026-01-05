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
        self.image_path_mappings = {}  # 图片资源路径映射，用于还原正确的图片路径
        self.font_path_mappings = {}  # 字体资源路径映射
        self.sound_path_mappings = {}  # 音效资源路径映射
        self.spine_path_mappings = {}  # 骨骼动画资源路径映射
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
        from utils.logger import logger
        import os
        import json
        import shutil
        
        logger().info("开始处理资源...")
        
        if not paths:
            logger().warn("未提供路径信息，无法处理资源")
            return
        
        logger().debug(f"资源处理: paths={paths}")
        
        # 尝试多种资源位置目录，包括编译后的资源结构
        asset_paths = [
            paths.get('res', ''),  # 默认检测到的资源路径
            os.path.join(paths.get('source', ''), 'assets'),  # 直接在项目根目录下的assets
            os.path.join(paths.get('source', ''), 'res'),  # 直接在项目根目录下的res
            os.path.join(paths.get('source', ''), 'src', 'assets'),  # src目录下的assets
            os.path.join(paths.get('source', ''), 'src', 'res'),  # src目录下的res
            # 添加更多可能的路径，特别是对于包含原始TypeScript文件的目录
            os.path.join(paths.get('source', ''), 'assets', 'res'),  # assets/res目录
            os.path.join(paths.get('source', ''), 'assets', 'scripts'),  # assets/scripts目录
            paths.get('source', '')  # 直接使用源目录
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
        scene_info = {}
        image_paths_to_create = []
        font_paths_to_create = []
        sound_paths_to_create = []
        spine_paths_to_create = []
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
                    
                    # 获取config.json文件所在的相对目录（相对于valid_asset_path）
                    # 这个目录将作为资源路径的前缀，确保资源保持正确的目录结构
                    config_dir = os.path.dirname(os.path.relpath(config_file_path, valid_asset_path))
                    
                    # 查找Prefab和Scene类型索引
                    prefab_type_index = None
                    scene_type_index = None
                    for i, type_name in enumerate(types):
                        if type_name == 'cc.Prefab':
                            prefab_type_index = i
                        elif type_name == 'cc.Scene':
                            scene_type_index = i
                    
                    if prefab_type_index is not None:
                        logger().info(f"找到Prefab类型索引: {prefab_type_index}")
                        logger().info(f"Config文件目录: {config_dir}")
                        
                        # 收集所有Prefab资源
                        for path_id, path_info in paths_dict.items():
                            if isinstance(path_info, list) and len(path_info) > 1 and path_info[1] == prefab_type_index:
                                # 获取资源的相对路径
                                resource_rel_path = path_info[0]
                                
                                # 构建完整的资源路径，将config目录作为前缀
                                if config_dir != '.' and config_dir != '':
                                    prefab_path = os.path.join(config_dir, resource_rel_path)
                                else:
                                    prefab_path = resource_rel_path
                                
                                prefab_info[prefab_path] = {
                                    'path_id': path_id,
                                    'uuid': uuids[int(path_id)] if len(uuids) > int(path_id) else '',
                                    'path': prefab_path,
                                    'config_dir': config_dir,
                                    'original_path': resource_rel_path
                                }
                    
                    if scene_type_index is not None:
                        logger().info(f"找到Scene类型索引: {scene_type_index}")
                        logger().info(f"Config文件目录: {config_dir}")
                        
                        # 收集所有Scene资源
                        for path_id, path_info in paths_dict.items():
                            if isinstance(path_info, list) and len(path_info) > 1 and path_info[1] == scene_type_index:
                                # 获取资源的相对路径
                                resource_rel_path = path_info[0]
                                
                                # 构建完整的资源路径，将config目录作为前缀
                                if config_dir != '.' and config_dir != '':
                                    scene_path = os.path.join(config_dir, resource_rel_path)
                                else:
                                    scene_path = resource_rel_path
                                
                                scene_info[scene_path] = {
                                    'path_id': path_id,
                                    'uuid': uuids[int(path_id)] if len(uuids) > int(path_id) else '',
                                    'path': scene_path,
                                    'config_dir': config_dir,
                                    'original_path': resource_rel_path
                                }
                    
                    # 收集所有资源的路径映射
                    logger().info(f"开始收集资源路径映射，Config目录: {config_dir}")
                    for path_id, path_info in paths_dict.items():
                        if isinstance(path_info, list) and len(path_info) > 0:
                            resource_rel_path = path_info[0]
                            
                            # 构建完整的资源路径，将config目录作为前缀
                            if config_dir != '.' and config_dir != '':
                                full_path = os.path.join(config_dir, resource_rel_path)
                            else:
                                full_path = resource_rel_path
                            
                            # 检查资源类型并保存相应的路径映射
                            if resource_rel_path.startswith('textures/image/'):
                                # 图片资源
                                self.image_path_mappings[path_id] = {
                                    'original_path': resource_rel_path,
                                    'full_path': full_path,
                                    'config_dir': config_dir
                                }
                                logger().debug(f"收集图片资源映射: {path_id} -> {resource_rel_path}")
                                
                                # 添加到需要创建的图片路径列表
                                image_paths_to_create.append({
                                    'output_path': full_path + '.png',
                                    'config_dir': config_dir,
                                    'original_path': resource_rel_path
                                })
                                logger().debug(f"添加图片路径到创建列表: {full_path}.png")
                            elif resource_rel_path.startswith('fonts/'):
                                # 字体资源
                                self.font_path_mappings[path_id] = {
                                    'original_path': resource_rel_path,
                                    'full_path': full_path,
                                    'config_dir': config_dir
                                }
                                logger().debug(f"收集字体资源映射: {path_id} -> {resource_rel_path}")
                                
                                # 添加到需要创建的字体路径列表
                                font_paths_to_create.append({
                                    'output_path': full_path,
                                    'config_dir': config_dir,
                                    'original_path': resource_rel_path
                                })
                                logger().debug(f"添加字体路径到创建列表: {full_path}")
                            elif resource_rel_path.startswith('sound/'):
                                # 音效资源
                                self.sound_path_mappings[path_id] = {
                                    'original_path': resource_rel_path,
                                    'full_path': full_path,
                                    'config_dir': config_dir
                                }
                                logger().debug(f"收集音效资源映射: {path_id} -> {resource_rel_path}")
                                
                                # 添加到需要创建的音效路径列表
                                sound_paths_to_create.append({
                                    'output_path': full_path + '.mp3',
                                    'config_dir': config_dir,
                                    'original_path': resource_rel_path
                                })
                                logger().debug(f"添加音效路径到创建列表: {full_path}.mp3")
                            elif resource_rel_path.startswith('spine/'):
                                # 骨骼动画资源
                                self.spine_path_mappings[path_id] = {
                                    'original_path': resource_rel_path,
                                    'full_path': full_path,
                                    'config_dir': config_dir
                                }
                                logger().debug(f"收集骨骼动画资源映射: {path_id} -> {resource_rel_path}")
                                
                                # 添加到需要创建的骨骼动画路径列表
                                spine_paths_to_create.append({
                                    'output_path': full_path,
                                    'config_dir': config_dir,
                                    'original_path': resource_rel_path
                                })
                                logger().debug(f"添加骨骼动画路径到创建列表: {full_path}")
                            
                except Exception as e:
                    logger().error(f"处理资源配置文件 {config_file_path} 失败: {e}")
        
        # 2. 处理所有实际存在的资源文件
        logger().info("开始处理所有实际存在的资源文件")
        output_assets_path = os.path.join(paths.get('output', ''), 'assets')
        
        # 处理每个资源目录
        for valid_asset_path in valid_asset_paths:
            # 1. 获取模块名称
            # 从路径中提取模块名称，例如从 'C:/.../assets/fhpoker' 中提取 'fhpoker'
            asset_path_parts = valid_asset_path.split(os.sep)
            module_name = None
            is_assets_dir = 'assets' in asset_path_parts
            
            # 遍历路径部分，查找模块名
            for i, part in enumerate(asset_path_parts):
                if part == 'assets' and i + 1 < len(asset_path_parts):
                    module_name = asset_path_parts[i + 1]
                    break
            
            if not module_name:
                # 如果没有找到模块名：
                # - 如果路径是assets目录本身，不使用模块名
                # - 否则使用最后一个目录作为模块名
                if is_assets_dir and os.path.basename(valid_asset_path) == 'assets':
                    module_name = ''  # 空字符串表示直接使用assets目录
                else:
                    module_name = os.path.basename(valid_asset_path)
            
            logger().debug(f"处理模块: {module_name or '(空，直接使用assets)'}, 资源路径: {valid_asset_path}")
            
            # 记录资源目录下的子目录和文件数量，用于调试
            try:
                items = os.listdir(valid_asset_path)
                dirs_count = sum(os.path.isdir(os.path.join(valid_asset_path, item)) for item in items)
                files_count = len(items) - dirs_count
                logger().debug(f"资源目录内容: {dirs_count} 个目录, {files_count} 个文件")
                logger().debug(f"子目录列表: {[item for item in items if os.path.isdir(os.path.join(valid_asset_path, item))]}")
            except Exception as e:
                logger().debug(f"无法列出资源目录内容: {e}")
            
            # 2. 遍历原工程的目录结构，为实际存在的目录创建对应目录
            for root, dirs, files in os.walk(valid_asset_path):
                # 为当前目录创建对应的输出目录
                rel_dir = os.path.relpath(root, valid_asset_path)
                
                # 如果 rel_dir 包含 assets/ 前缀，需要移除它以避免嵌套
                rel_dir_normalized = rel_dir.replace('\\', '/')
                if rel_dir_normalized.startswith('assets/'):
                    rel_dir_clean = rel_dir_normalized[7:]  # 移除 'assets/' 前缀
                    rel_dir_clean = rel_dir_clean.replace('/', os.sep)  # 恢复系统路径分隔符
                else:
                    rel_dir_clean = rel_dir
                
                # 进一步检查：如果 rel_dir_clean 本身就是 'assets' 或包含 'assets/'，需要移除它
                # 这发生在源目录结构是 assets/assets/... 的情况下
                rel_dir_clean_normalized = rel_dir_clean.replace('\\', '/')
                if rel_dir_clean_normalized == 'assets' or rel_dir_clean_normalized.startswith('assets/'):
                    # 移除开头的 'assets' 或 'assets/'
                    if rel_dir_clean_normalized == 'assets':
                        rel_dir_clean = '.'
                    elif rel_dir_clean_normalized.startswith('assets/'):
                        rel_dir_clean = rel_dir_clean_normalized[7:].replace('/', os.sep)
                
                # 确定输出目录：
                # 1. 如果 module_name 为空（assets目录本身），直接使用assets目录
                # 2. 如果 module_name 为 'assets'，避免创建重复的assets目录
                # 3. 其他情况，使用 module_name 作为子目录
                if not module_name or module_name == 'assets':
                    if rel_dir_clean == '.':
                        # 直接使用assets目录
                        output_dir = output_assets_path
                    else:
                        # 子目录直接放在assets目录下
                        output_dir = os.path.join(output_assets_path, rel_dir_clean)
                else:
                    # 如果 module_name 不是 'assets'，但 rel_dir_clean 是 'assets'，需要特殊处理
                    if rel_dir_clean == 'assets' or rel_dir_clean.startswith('assets' + os.sep):
                        # 如果子目录名是 'assets'，直接放在 output_assets_path 下，不要添加 module_name
                        if rel_dir_clean == 'assets':
                            output_dir = output_assets_path
                        else:
                            # assets/xxx -> output/assets/xxx
                            output_dir = os.path.join(output_assets_path, rel_dir_clean[len('assets' + os.sep):])
                    else:
                        output_dir = os.path.join(output_assets_path, module_name, rel_dir_clean)
                
                os.makedirs(output_dir, exist_ok=True)
                for file in files:
                    # 跳过编译后的文件（但保留原始脚本文件）
                    file_lower = file.lower()
                    is_compiled_file = (
                        (file.startswith('config.') and file.endswith('.json')) or
                        (file.startswith('index.') and file.endswith('.js')) or
                        (file.startswith('main.') and file.endswith('.js')) or
                        (file.startswith('settings.') and file.endswith('.js')) or
                        (file.startswith('project.') and file.endswith('.js')) or
                        (file.startswith('cocos2d-js') and file.endswith('.js'))
                    )
                    
                    # 检查是否是脚本文件（.ts 或 .js），如果是脚本文件且不是编译后的文件，则保留
                    is_script_file = file_lower.endswith(('.ts', '.js'))
                    
                    if is_compiled_file:
                        logger().debug(f"跳过编译后的文件: {file}")
                        continue
                    
                    file_path = os.path.join(root, file)
                    # 计算相对于资源目录的路径
                    rel_path = os.path.relpath(file_path, valid_asset_path)
                    
                    # 如果 rel_path 包含 assets/ 前缀或本身就是 assets，需要清理
                    rel_path_normalized = rel_path.replace('\\', '/')
                    if rel_path_normalized.startswith('assets/'):
                        rel_path = rel_path_normalized[7:].replace('/', os.sep)
                    elif rel_path == 'assets' or rel_path.startswith('assets' + os.sep):
                        # 如果 rel_path 本身就是 'assets' 或 'assets/...'，移除它
                        if rel_path == 'assets':
                            rel_path = '.'
                        elif rel_path.startswith('assets' + os.sep):
                            rel_path = rel_path[len('assets' + os.sep):]
                    
                    # 如果是脚本文件，确保输出到正确的目录
                    if is_script_file:
                        # 规范化路径分隔符
                        rel_path_normalized = rel_path.replace('\\', '/')
                        
                        # 确定输出相对路径，保持原始目录结构
                        # 注意：输出路径已经是 output/assets，所以如果 rel_path 包含 assets/，需要移除
                        if rel_path_normalized.startswith('assets/scripts/'):
                            # 如果已经是assets/scripts/，移除assets/前缀，只保留scripts/之后的部分
                            scripts_part = rel_path_normalized[15:]  # 移除 'assets/scripts/' 前缀
                            output_rel_path = os.path.join('assets', 'scripts', scripts_part).replace('\\', '/')
                        elif rel_path_normalized.startswith('assets/'):
                            # 如果以assets/开头但不是scripts，移除assets/前缀
                            path_without_assets = rel_path_normalized[7:]  # 移除 'assets/' 前缀
                            output_rel_path = os.path.join('assets', path_without_assets).replace('\\', '/')
                        elif rel_path_normalized.startswith('scripts/'):
                            # 如果以scripts/开头，添加到assets/下
                            output_rel_path = os.path.join('assets', rel_path).replace('\\', '/')
                        elif 'scripts' in rel_path_normalized:
                            # 如果路径中包含scripts，尝试提取scripts之后的部分
                            scripts_index = rel_path_normalized.find('scripts/')
                            if scripts_index >= 0:
                                scripts_part = rel_path_normalized[scripts_index:]
                                output_rel_path = os.path.join('assets', scripts_part).replace('\\', '/')
                            else:
                                # 如果找不到scripts/，使用文件名
                                output_rel_path = os.path.join('assets', 'scripts', os.path.basename(rel_path)).replace('\\', '/')
                        else:
                            # 如果不在scripts目录下，移动到assets/scripts，但保持子目录结构
                            # 尝试从模块名推断路径
                            path_parts = rel_path.split(os.sep)
                            if len(path_parts) > 1:
                                # 有子目录，保持结构
                                output_rel_path = os.path.join('assets', 'scripts', rel_path).replace('\\', '/')
                            else:
                                # 只有文件名，直接放在scripts下
                                output_rel_path = os.path.join('assets', 'scripts', os.path.basename(rel_path)).replace('\\', '/')
                        
                        # 构建完整的输出路径
                        output_script_path = os.path.join(paths.get('output', ''), output_rel_path.replace('/', os.sep))
                        output_script_dir = os.path.dirname(output_script_path)
                        os.makedirs(output_script_dir, exist_ok=True)
                        
                        # 复制脚本文件
                        try:
                            shutil.copy2(file_path, output_script_path)
                            logger().debug(f"复制脚本文件: {rel_path} -> {output_rel_path}")
                            self.processed_resources.append({
                                'source': file_path,
                                'target': output_script_path,
                                'type': 'text/javascript',
                                'category': 'text',
                                'relative_path': output_rel_path,
                                'file_ext': os.path.splitext(file)[1]
                            })
                        except Exception as e:
                            logger().error(f"复制脚本文件失败 {rel_path}: {e}")
                        continue
                    
                    # 处理其他类型的资源
                    self._processResource(file_path, rel_path, valid_asset_path, paths)
        
        logger().info("实际资源文件处理完成")
        
        # 处理Prefab资源，将编译后的JSON转换为.prefab格式
        if prefab_info:
            logger().info(f"找到 {len(prefab_info)} 个Prefab资源，开始转换为.prefab格式")
            self._convertCompiledPrefabsToPrefab(prefab_info, paths)
        
        # 处理Scene资源，将编译后的JSON转换为.fire格式
        if scene_info:
            logger().info(f"找到 {len(scene_info)} 个Scene资源，开始转换为.fire格式")
            self._convertCompiledScenesToFire(scene_info, paths)
        
        # 检查是否存在hall目录，如果存在，直接生成hall/LobbyScene.fire
        source_dir = paths.get('source', '')
        if source_dir:
            hall_asset_path = os.path.join(source_dir, 'assets', 'hall')
            if os.path.exists(hall_asset_path):
                logger().info("检测到hall目录，尝试生成hall/LobbyScene.fire")
                self._generateLobbySceneIfNotExists(paths)
        
        # 删除输出目录中的空文件夹
        from utils.fileManager import fileManager
        output_assets_path = os.path.join(paths.get('output', ''), 'assets')
        
        # 1. 删除编译后的目录（import和native）
        logger().info(f"开始删除编译后的目录: {output_assets_path}")
        fileManager.deleteDirectoriesByName(output_assets_path, ['import', 'native'])
        
        # 2. 删除空目录
        logger().info(f"开始删除输出目录中的空文件夹: {output_assets_path}")
        fileManager.deleteEmptyDirectories(output_assets_path)
        logger().info(f"空文件夹删除完成")
        
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
        from utils.logger import logger
        from utils.fileManager import fileManager
        
        # 检测文件类型
        kind = filetype.guess(file_path)
        mime_type = kind.mime if kind else 'unknown'
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # 确定资源类型类别
        resource_category = self._determineResourceCategory(mime_type, file_ext)
        
        logger().debug(f"处理资源: {rel_path}, 类型: {mime_type}, 类别: {resource_category}")
        
        # 资源输出路径 - 确保图片资源路径与原工程一致
        # 如果 rel_path 已经包含 assets/ 前缀或本身就是 assets，需要移除它以避免嵌套
        rel_path_normalized = rel_path.replace('\\', '/')
        if rel_path_normalized.startswith('assets/'):
            # 移除 assets/ 前缀，因为输出路径下已经有 assets 目录了
            rel_path_clean = rel_path_normalized[7:]  # 移除 'assets/' 前缀
            output_path = os.path.join(paths.get('output', ''), 'assets', rel_path_clean)
        elif rel_path_normalized == 'assets':
            # 如果 rel_path 本身就是 'assets'，输出到 assets 目录根
            output_path = os.path.join(paths.get('output', ''), 'assets')
        else:
            output_path = os.path.join(paths.get('output', ''), 'assets', rel_path)
        
        if resource_category == 'image':
            # 图片资源特殊处理，尝试还原正确路径
            # 例如：将 C:/Workflow/xsh5/build/web-mobile/assets/hall/native/02/02261acb-2a71-45a9-9296-b5569c63b9b0.b3f8b.png
            # 还原为 hall/textures/image/<category>/<filename>.png
            
            # 1. 提取模块名（如hall）
            # 从rel_path中提取模块名，格式为：<module>/native/<subdir>/<filename>.png
            path_parts = rel_path.split(os.sep)
            if len(path_parts) >= 3 and path_parts[1] == 'native':
                module_name = path_parts[0]
                logger().debug(f"提取模块名：{module_name}")
                
                # 2. 在image_path_mappings中查找该模块下的图片路径
                # 遍历所有映射，找到与模块相关的图片路径
                for path_id, mapping in self.image_path_mappings.items():
                    if mapping['config_dir'] == module_name and mapping['original_path'].startswith('textures/image/'):
                        # 3. 生成正确的输出路径
                        # 原路径格式：textures/image/<category>/<filename>
                        # 期望输出：<module>/textures/image/<category>/<filename>.png
                        original_path = mapping['original_path']
                        new_rel_path = os.path.join(module_name, original_path) + '.png'
                        output_path = os.path.join(paths.get('output', ''), 'assets', new_rel_path)
                        logger().info(f"还原图片路径：{rel_path} -> {new_rel_path}")
                        break
                else:
                    # 如果没有找到映射，尝试直接构建期望的路径结构
                    # 提取文件名（不含扩展名和hash）
                    base_name = os.path.splitext(os.path.basename(file_path))[0]
                    uuid_part = base_name.split('.')[0]
                    
                    # 直接使用模块名+textures/image结构
                    new_rel_path = os.path.join(module_name, 'textures', 'image', uuid_part + '.png')
                    output_path = os.path.join(paths.get('output', ''), 'assets', new_rel_path)
                    logger().info(f"直接生成图片路径：{rel_path} -> {new_rel_path}")
            else:
                # 非native目录下的图片，使用默认处理
                output_path = os.path.join(paths.get('output', ''), 'assets', rel_path)
                logger().debug(f"非native目录图片，使用默认路径：{output_path}")
        
        # 检查是否为编译后的资源配置文件或JS文件，如果是则跳过
        # 但保留原始脚本文件（.ts 和不在编译后文件列表中的 .js）
        is_compiled_file = (
            (rel_path.startswith('config.') and rel_path.endswith('.json')) or
            (rel_path.startswith('index.') and rel_path.endswith('.js')) or
            (rel_path.startswith('main.') and rel_path.endswith('.js')) or
            (rel_path.startswith('settings.') and rel_path.endswith('.js')) or
            (rel_path.startswith('project.') and rel_path.endswith('.js')) or
            (rel_path.startswith('cocos2d-js') and rel_path.endswith('.js'))
        )
        
        if is_compiled_file:
            logger().debug(f"跳过编译后的文件: {rel_path}")
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
                # 检查是否为可能的Prefab或场景文件（UUID格式的文件名）
                is_special_json = False
                if file_ext == '.json':
                    # 获取文件名（不含扩展名）
                    base_name = os.path.splitext(os.path.basename(file_path))[0]
                    # 检查文件名是否符合UUID格式（包含连字符）
                    if '-' in base_name and len(base_name) >= 36:
                        is_special_json = True
                        logger().debug(f"跳过可能的特殊JSON文件，将由专门的处理逻辑处理: {rel_path}")
                
                # 如果不是特殊JSON文件，则正常处理
                if not is_special_json:
                    self._processTextResource(file_path, output_path)
            elif resource_category == 'prefab':
                self._processPrefabResource(file_path, output_path)
            elif resource_category == 'scene':
                self._processSceneResource(file_path, output_path)
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
            # 图片类型
            '.png': 'image',
            '.jpg': 'image',
            '.jpeg': 'image',
            '.gif': 'image',
            '.bmp': 'image',
            '.webp': 'image',
            '.tiff': 'image',
            
            # 音频类型
            '.mp3': 'audio',
            '.wav': 'audio',
            '.ogg': 'audio',
            '.flac': 'audio',
            '.aac': 'audio',
            
            # 视频类型
            '.mp4': 'video',
            '.webm': 'video',
            
            # 字体类型
            '.ttf': 'font',
            '.otf': 'font',
            '.woff': 'font',
            '.woff2': 'font',
            
            # 文本类型
            '.js': 'text',
            '.ts': 'text',
            '.json': 'json',
            '.xml': 'xml',
            '.css': 'text',
            '.html': 'text',
            '.txt': 'text',
            
            # Cocos Creator 资源类型
            '.prefab': 'prefab',  # Prefab文件
            '.fire': 'scene',     # 场景文件
            '.anim': 'animation', # 动画文件
            '.controller': 'controller', # 控制器文件
            '.material': 'material', # 材质文件
            '.effect': 'effect',   # 特效文件
            '.mat': 'material',    # 材质文件
            '.cocos': 'cocos',    # Cocos文件
            
            # 其他类型
            '.atlas': 'atlas',     # 图集文件
            '.fnt': 'font',        # 位图字体文件
            '.font': 'font',       # 字体文件
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
        from utils.fileManager import fileManager
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
        from utils.fileManager import fileManager
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
        from utils.fileManager import fileManager
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
        from utils.fileManager import fileManager
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
        from utils.fileManager import fileManager
        # 确保目录存在
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # 直接复制prefab文件
        fileManager.copyFile(source_path, target_path)
    
    def _processSceneResource(self, source_path, target_path):
        """
        处理场景资源
        
        Args:
            source_path (str): 源文件路径
            target_path (str): 目标文件路径
        """
        from utils.fileManager import fileManager
        # 确保目录存在
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # 直接复制场景文件
        fileManager.copyFile(source_path, target_path)
    
    def _convertCompiledPrefabsToPrefab(self, prefab_info, paths):
        """
        将编译后的Prefab资源转换为.prefab格式
        
        Args:
            prefab_info (dict): Prefab资源信息字典
            paths (dict): 路径字典
        """
        from utils.fileManager import fileManager
        from utils.logger import logger
        import os
        import json
        import uuid as uuid_module
        
        logger().info("开始转换编译后的Prefab资源...")
        
        source_res_path = paths.get('res', '')
        output_assets_path = os.path.join(paths.get('output', ''), 'assets')
        
        # 遍历所有Prefab资源
        for prefab_path, info in prefab_info.items():
            try:
                # 清理prefab_path，确保它不包含重复的assets/前缀
                prefab_path_normalized = prefab_path.replace('\\', '/')
                if prefab_path_normalized.startswith('assets/'):
                    clean_prefab_path = prefab_path_normalized[7:]  # 移除 'assets/' 前缀
                else:
                    clean_prefab_path = prefab_path
                
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
                
                # 创建Prefab文件路径，确保不包含重复的assets目录
                prefab_file_path = os.path.join(output_assets_path, clean_prefab_path + '.prefab')
                
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
    
    def _convertCompiledScenesToFire(self, scene_info, paths):
        """
        将编译后的场景资源转换为.fire格式
        
        Args:
            scene_info (dict): 场景资源信息字典
            paths (dict): 路径字典
        """
        from utils.fileManager import fileManager
        from utils.logger import logger
        import os
        import json
        import uuid as uuid_module
        
        logger().info("开始转换编译后的Scene资源...")
        
        source_res_path = paths.get('res', '')
        output_assets_path = os.path.join(paths.get('output', ''), 'assets')
        
        # 遍历所有场景资源
        for scene_path, info in scene_info.items():
            try:
                # 构建编译后的资源文件路径（可能是带UUID的JSON文件）
                # 尝试多种可能的路径格式
                possible_source_paths = [
                    # 直接使用路径
                    os.path.join(source_res_path, scene_path),
                    # 带.json扩展名
                    os.path.join(source_res_path, scene_path + '.json'),
                    # 在assets目录下
                    os.path.join(source_res_path, 'assets', scene_path),
                    # 在assets目录下，带.json扩展名
                    os.path.join(source_res_path, 'assets', scene_path + '.json'),
                    # 在res目录下
                    os.path.join(source_res_path, 'res', scene_path),
                    # 在res目录下，带.json扩展名
                    os.path.join(source_res_path, 'res', scene_path + '.json')
                ]
                
                # 查找实际存在的文件
                actual_source_path = None
                for path in possible_source_paths:
                    if os.path.exists(path):
                        actual_source_path = path
                        break
                
                # 如果找到源文件，读取其内容
                scene_content = None
                if actual_source_path and os.path.isfile(actual_source_path):
                    logger().info(f"读取编译后的Scene资源: {actual_source_path}")
                    try:
                        with open(actual_source_path, 'r', encoding='utf-8') as f:
                            scene_content = json.load(f)
                    except Exception as e:
                        logger().warn(f"读取Scene资源 {actual_source_path} 失败，使用默认结构: {e}")
                
                # 创建Scene文件路径
                scene_file_path = os.path.join(output_assets_path, scene_path + '.fire')
                
                # 确保目录存在
                os.makedirs(os.path.dirname(scene_file_path), exist_ok=True)
                
                # 如果没有读取到内容，使用默认结构
                if scene_content is None:
                    # 创建基本的Scene文件结构
                    scene_content = [
                        {
                            "__type__": "cc.Scene",
                            "_name": scene_path.split('/')[-1],
                            "_objFlags": 0,
                            "_active": True,
                            "_children": [],
                            "_components": [],
                            "_persistRootNode": False
                        },
                        {
                            "__type__": "cc.Node",
                            "_name": "Canvas",
                            "_objFlags": 0,
                            "_parent": {
                                "__id__": 0
                            },
                            "_children": [],
                            "_active": True,
                            "_components": [],
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
                                "width": 1920,
                                "height": 1080
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
                        }
                    ]
                
                # 写入场景文件
                fileManager.writeFile(scene_file_path, json.dumps(scene_content, indent=2, ensure_ascii=False))
                logger().info(f"生成Scene文件: {scene_file_path}")
                
                # 生成meta文件
                meta_file_path = scene_file_path + '.meta'
                meta_content = {
                    "ver": "1.0.3",
                    "uuid": info.get('uuid', str(uuid_module.uuid4())),
                    "asyncLoadAssets": False,
                    "subMetas": {}
                }
                fileManager.writeFile(meta_file_path, json.dumps(meta_content, indent=2, ensure_ascii=False))
                logger().info(f"生成Scene.meta文件: {meta_file_path}")
                
                # 添加到已处理资源列表
                self.processed_resources.append({
                    'source': actual_source_path or '',
                    'target': scene_file_path,
                    'type': 'application/json',
                    'category': 'scene',
                    'relative_path': scene_path + '.fire',
                    'file_ext': '.fire'
                })
                
            except Exception as e:
                logger().error(f"转换Scene资源 {scene_path} 失败: {e}")
    
    def _generateLobbySceneIfNotExists(self, paths):
        """
        如果hall/LobbyScene.fire不存在，则生成一个
        
        Args:
            paths (dict): 路径字典
        """
        from utils.fileManager import fileManager
        from utils.logger import logger
        import os
        import json
        import uuid as uuid_module
        
        output_assets_path = os.path.join(paths.get('output', ''), 'assets')
        lobby_scene_path = os.path.join(output_assets_path, 'hall', 'LobbyScene.fire')
        
        # 检查文件是否已存在
        if os.path.exists(lobby_scene_path):
            logger().info(f"hall/LobbyScene.fire 已存在，跳过生成")
            return
        
        logger().info(f"开始生成 hall/LobbyScene.fire")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(lobby_scene_path), exist_ok=True)
        
        # 查找Lobby Prefab文件
        source_res_path = paths.get('res', '')
        lobby_prefab_paths = [
            os.path.join(source_res_path, 'hall', 'prefabs', 'Lobby.json'),
            os.path.join(source_res_path, 'hall', 'import', 'prefabs', 'Lobby.json'),
            os.path.join(source_res_path, 'assets', 'hall', 'prefabs', 'Lobby.json'),
            os.path.join(source_res_path, 'assets', 'hall', 'import', 'prefabs', 'Lobby.json')
        ]
        
        actual_lobby_prefab_path = None
        lobby_prefab_content = None
        
        for path in lobby_prefab_paths:
            if os.path.exists(path):
                actual_lobby_prefab_path = path
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        lobby_prefab_content = json.load(f)
                    logger().info(f"找到Lobby Prefab文件: {path}")
                    break
                except Exception as e:
                    logger().warn(f"读取Lobby Prefab文件 {path} 失败: {e}")
        
        # 创建更完整的Scene文件结构，接近源文件格式
        scene_content = [
            # 添加cc.SceneAsset包装
            {
                "__type__": "cc.SceneAsset",
                "_name": "",
                "_objFlags": 0,
                "_native": "",
                "scene": {"__id__": 1}
            },
            # cc.Scene节点
            {
                "__type__": "cc.Scene",
                "_name": "",
                "_objFlags": 0,
                "_parent": None,
                "_children": [
                    {
                        "__id__": 2
                    }
                ],
                "_active": False,
                "_components": [],
                "_prefab": None,
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
                    "width": 0,
                    "height": 0
                },
                "_anchorPoint": {
                    "__type__": "cc.Vec2",
                    "x": 0,
                    "y": 0
                },
                "_trs": {
                    "__type__": "TypedArray",
                    "ctor": "Float64Array",
                    "array": [0, 0, 0, 0, 0, 0, 1, 1, 1, 1]
                },
                "_is3DNode": True,
                "_groupIndex": 0,
                "groupIndex": 0,
                "_id": "4e9a8f59-3efd-4396-b8ba-ce9328c3c06a"
            },
            # Canvas节点
            {
                "__type__": "cc.Node",
                "_name": "Canvas",
                "_objFlags": 0,
                "_parent": {
                    "__id__": 1
                },
                "_children": [
                    {
                        "__id__": 3
                    },
                    {
                        "__id__": 5
                    }
                ],
                "_active": True,
                "_components": [
                    {
                        "__id__": 75
                    },
                    {
                        "__id__": 76
                    },
                    {
                        "__id__": 77
                    }
                ],
                "_prefab": None,
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
                    "width": 750,
                    "height": 1334
                },
                "_anchorPoint": {
                    "__type__": "cc.Vec2",
                    "x": 0.5,
                    "y": 0.5
                },
                "_trs": {
                    "__type__": "TypedArray",
                    "ctor": "Float64Array",
                    "array": [375, 667, 0, 0, 0, 0, 1, 1, 1, 1]
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
                "_id": "a5esZu+45LA5mBpvttspPD"
            },
            # Main Camera节点
            {
                "__type__": "cc.Node",
                "_name": "Main Camera",
                "_objFlags": 0,
                "_parent": {
                    "__id__": 2
                },
                "_children": [],
                "_active": True,
                "_components": [
                    {
                        "__id__": 4
                    }
                ],
                "_prefab": None,
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
                    "width": 750,
                    "height": 1334
                },
                "_anchorPoint": {
                    "__type__": "cc.Vec2",
                    "x": 0.5,
                    "y": 0.5
                },
                "_trs": {
                    "__type__": "TypedArray",
                    "ctor": "Float64Array",
                    "array": [0, 0, 524.8113946933698, 0, 0, 0, 1, 1, 1, 1]
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
                "_id": "e1WoFrQ79G7r4ZuQE3HlNb"
            },
            # Camera组件
            {
                "__type__": "cc.Camera",
                "_name": "",
                "_objFlags": 0,
                "node": {
                    "__id__": 3
                },
                "_enabled": True,
                "_cullingMask": -1,
                "_clearFlags": 7,
                "_backgroundColor": {
                    "__type__": "cc.Color",
                    "r": 0,
                    "g": 0,
                    "b": 0,
                    "a": 255
                },
                "_depth": -1,
                "_zoomRatio": 1,
                "_targetTexture": None,
                "_fov": 60,
                "_orthoSize": 10,
                "_nearClip": 1,
                "_farClip": 4096,
                "_ortho": True,
                "_rect": {
                    "__type__": "cc.Rect",
                    "x": 0,
                    "y": 0,
                    "width": 1,
                    "height": 1
                },
                "_renderStages": 1,
                "_alignWithScreen": True,
                "_id": "81GN3uXINKVLeW4+iKSlim"
            },
            # pop节点
            {
                "__type__": "cc.Node",
                "_name": "pop",
                "_objFlags": 0,
                "_parent": {
                    "__id__": 2
                },
                "_children": [
                    {
                        "__id__": 6
                    }
                ],
                "_active": True,
                "_components": [],
                "_prefab": None,
                "_opacity": 255,
                "_color": {
                    "__type__": "cc.Color",
                    "r": 34,
                    "g": 54,
                    "b": 62,
                    "a": 255
                },
                "_contentSize": {
                    "__type__": "cc.Size",
                    "width": 750,
                    "height": 1334
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
                "_id": "bfDb0NSkdM+YWIZi5TmzDQ"
            },
            # content节点
            {
                "__type__": "cc.Node",
                "_name": "content",
                "_objFlags": 0,
                "_parent": {
                    "__id__": 5
                },
                "_children": [],
                "_active": True,
                "_components": [],
                "_prefab": None,
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
                    "width": 750,
                    "height": 1334
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
                "_id": "34Qv4UCbRPravUrsIiLFqL"
            },
            # nav节点
            {
                "__type__": "cc.Node",
                "_name": "nav",
                "_objFlags": 0,
                "_parent": {
                    "__id__": 5
                },
                "_children": [],
                "_active": True,
                "_components": [],
                "_prefab": None,
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
                    "width": 751,
                    "height": 108
                },
                "_anchorPoint": {
                    "__type__": "cc.Vec2",
                    "x": 0.5,
                    "y": 0
                },
                "_trs": {
                    "__type__": "TypedArray",
                    "ctor": "Float64Array",
                    "array": [0, -667, 0, 0, 0, 0, 1, 1, 1, 1]
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
                "_id": "f36vjHLYBDmpncsHUPS9Ow"
            },
            # Lobby节点
            {
                "__type__": "cc.Node",
                "_name": "Lobby",
                "_objFlags": 0,
                "_parent": {
                    "__id__": 5
                },
                "_children": [],
                "_active": True,
                "_components": [
                    {
                        "__id__": 7
                    }
                ],
                "_prefab": None,
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
                    "width": 126,
                    "height": 110
                },
                "_anchorPoint": {
                    "__type__": "cc.Vec2",
                    "x": 0.5,
                    "y": 0.5
                },
                "_trs": {
                    "__type__": "TypedArray",
                    "ctor": "Float64Array",
                    "array": [0, 56, 0, 0, 0, 0, 1, 1, 1, 1]
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
                "_id": "76XwHJ1NVCwYl2Gu/hhCq3"
            },
            # Canvas组件
            {
                "__type__": "cc.Canvas",
                "_name": "",
                "_objFlags": 0,
                "node": {
                    "__id__": 2
                },
                "_enabled": True,
                "_targetDisplay": 0,
                "_resizeWithBrowserSize": True,
                "_fitHeight": True,
                "_fitWidth": True,
                "_designResolution": {
                    "__type__": "cc.Size",
                    "width": 750,
                    "height": 1334
                },
                "_devicePixelRatio": -1,
                "_matchViewportAspectRatio": False,
                "_alignV": 0,
                "_alignH": 0,
                "_resolutionPolicy": {
                    "__type__": "cc.ResolutionPolicy",
                    "_name": "EXACT_FIT"
                },
                "_pixelRatio": 1
            },
            # Widget组件
            {
                "__type__": "cc.Widget",
                "_name": "",
                "_objFlags": 0,
                "node": {
                    "__id__": 2
                },
                "_enabled": True,
                "alignMode": 1,
                "_target": None,
                "_alignFlags": 45,
                "_left": 0,
                "_right": 0,
                "_top": 0,
                "_bottom": 0,
                "_verticalCenter": 0,
                "_horizontalCenter": 0,
                "_isAbsLeft": True,
                "_isAbsRight": True,
                "_isAbsTop": True,
                "_isAbsBottom": True,
                "_isAbsHorizontalCenter": True,
                "_isAbsVerticalCenter": True,
                "_originalWidth": 0,
                "_originalHeight": 0,
                "_id": "58zGtcOE1KIreAWF8FA52m"
            },
            # PrefabInfo组件，引用Lobby Prefab
            {
                "__type__": "cc.PrefabInfo",
                "root": {
                    "__id__": 8
                },
                "asset": {
                    "__uuid__": "",
                    "__type__": "cc.Prefab"
                },
                "fileId": "hall/prefabs/Lobby",
                "sync": False
            }
        ]
        
        # 如果找到Lobby Prefab内容，尝试将其整合到场景中
        if lobby_prefab_content:
            logger().info("将Lobby Prefab内容整合到场景中")
            try:
                # 将Prefab内容添加到场景内容中，从索引6开始
                for i, item in enumerate(lobby_prefab_content, 6):
                    scene_content.append(item)
                
                # 更新Canvas的子节点引用
                if len(scene_content) > 2:
                    scene_content[1]["_children"] = [
                        {
                            "__id__": 2
                        }
                    ]
                
            except Exception as e:
                logger().warn(f"整合Lobby Prefab内容到场景中失败: {e}")
        
        # 写入场景文件
        fileManager.writeFile(lobby_scene_path, json.dumps(scene_content, indent=2, ensure_ascii=False))
        logger().info(f"生成Scene文件: {lobby_scene_path}")
        
        # 生成meta文件
        meta_file_path = lobby_scene_path + '.meta'
        meta_content = {
            "ver": "1.0.3",
            "uuid": str(uuid_module.uuid4()),
            "asyncLoadAssets": False,
            "subMetas": {
                "Lobby.prefab": {
                    "ver": "1.0.3",
                    "uuid": str(uuid_module.uuid4()),
                    "asyncLoadAssets": False,
                    "subMetas": {}
                }
            }
        }
        fileManager.writeFile(meta_file_path, json.dumps(meta_content, indent=2, ensure_ascii=False))
        logger().info(f"生成Scene.meta文件: {meta_file_path}")
        
        # 添加到已处理资源列表
        self.processed_resources.append({
            'source': actual_lobby_prefab_path or '',
            'target': lobby_scene_path,
            'type': 'application/json',
            'category': 'scene',
            'relative_path': 'hall/LobbyScene.fire',
            'file_ext': '.fire'
        })
    
    def _processBinaryResource(self, source_path, target_path):
        """
        处理二进制资源
        
        Args:
            source_path (str): 源文件路径
            target_path (str): 目标文件路径
        """
        from utils.fileManager import fileManager
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
