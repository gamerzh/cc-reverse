#!/usr/bin/env python3
"""
资源处理器 - 参考Cocos Creator Web逆向工程实现
"""

import os
import json
import uuid
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

# 本地实现logger函数
def logger():
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

# 本地实现uuidUtils类
class UuidUtils:
    """UUID工具类"""
    
    @staticmethod
    def generate_uuid():
        """生成UUID"""
        return str(uuid.uuid4())
    
    @staticmethod
    def decode_uuid(uuid_str: str) -> str:
        """解码UUID"""
        return uuid_str

# 本地实现fileManager类
class FileManager:
    """文件管理器类"""
    
    def __init__(self, output_path: str, bundle_filter: str = None):
        self.output_path = output_path
        self.bundle_filter = bundle_filter
        # 记录已生成.meta的目录，避免重复生成
        self.generated_dir_metas = set()
    
    def ensure_directory_exists(self, dir_path: str):
        """确保目录存在"""
        os.makedirs(dir_path, exist_ok=True)
    
    def write_file(self, directory: str, filename: str, content: Any):
        """写入文件"""
        # 构建完整路径 - 资源文件夹和bundle的脚本文件夹同级，不需要再套一层
        full_dir = os.path.join(self.output_path, 'assets', directory)
        
        self.ensure_directory_exists(full_dir)
        
        # 生成目录的.meta文件（如果还没有生成）
        self.write_directory_meta(directory)
        
        full_path = os.path.join(full_dir, filename)
        
        if isinstance(content, dict):
            # 写入JSON文件
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
        elif isinstance(content, str):
            # 写入文本文件
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
        else:
            # 写入二进制文件
            with open(full_path, 'wb') as f:
                f.write(content)
        
        logger()['debug'](f"写入文件: {full_path}")
    
    def write_directory_meta(self, directory: str):
        """写入目录的.meta文件"""
        # 避免重复生成
        if directory in self.generated_dir_metas:
            return
        
        # 构建完整目录路径 - 资源文件夹和bundle的脚本文件夹同级，不需要再套一层
        full_dir = os.path.join(self.output_path, 'assets', directory)
        
        # 生成目录.meta文件内容
        dir_meta_content = {
            "ver": "1.2.7",
            "uuid": str(uuid.uuid4()),
            "optimizationPolicy": "AUTO",
            "asyncLoadAssets": False,
            "readonly": False,
            "subMetas": {}
        }
        
        # 写入目录.meta文件
        meta_file_path = os.path.join(full_dir, '.meta')
        with open(meta_file_path, 'w', encoding='utf-8') as f:
            json.dump(dir_meta_content, f, indent=2, ensure_ascii=False)
        
        logger()['debug'](f"写入目录.meta文件: {meta_file_path}")
        self.generated_dir_metas.add(directory)
        
        # 递归生成父目录的.meta文件
        parent_dir = os.path.dirname(directory)
        if parent_dir and parent_dir != '.':
            self.write_directory_meta(parent_dir)
    
    def copy_file(self, source_path: str, target_path: str):
        """复制文件"""
        self.ensure_directory_exists(os.path.dirname(target_path))
        shutil.copy2(source_path, target_path)
        logger()['debug'](f"复制文件: {source_path} -> {target_path}")

# 本地实现converters类
class Converters:
    """资源转换器类"""
    
    @staticmethod
    def convert_sprite_atlas(sprite_frames: Dict[str, Any]):
        """
        转换精灵图集
        """
        logger()['info'](f"转换精灵图集，共 {len(sprite_frames)} 个精灵帧")
        # 遍历所有精灵帧
        for key, frame_data in sprite_frames.items():
            # 处理精灵帧数据
            if isinstance(frame_data, dict):
                Converters.process_sprite_frame_data(key, frame_data)
    
    @staticmethod
    def process_sprite_frame_data(key: str, frame_data: Dict[str, Any]):
        """
        处理单个精灵帧数据
        """
        # 这里可以添加精灵帧数据处理逻辑
        logger()['debug'](f"处理精灵帧数据: {key}")
    
    @staticmethod
    def json_to_plist(file_name: str):
        """
        将JSON转换为PLIST格式
        
        Args:
            file_name (str): 文件名（不含扩展名）
        """
        try:
            # 读取JSON文件
            with open(f"{file_name}.json", 'r', encoding='utf-8') as f:
                data = f.read()
            json_data = json.loads(data)
            
            # 添加必要的属性
            enhanced_json = Converters.add_properties(json_data, file_name)
            
            # 创建XML文档
            xml = Converters.create_xml_document(enhanced_json)
            
            # 写入PLIST文件
            with open(f"{file_name}.plist", 'w', encoding='utf-8') as f:
                f.write(xml)
            
            logger()['debug'](f"转换完成: {file_name}.json -> {file_name}.plist")
        except Exception as e:
            logger()['exception'](f"转换文件 {file_name} 时出错", e)
    
    @staticmethod
    def create_xml_document(json_data: Dict[str, Any]) -> str:
        """
        创建XML文档
        
        Args:
            json_data (dict): JSON对象
            
        Returns:
            str: XML文档字符串
        """
        xml = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">',
               '<plist version="1.0">',
               '<dict>']
        
        # 递归处理JSON数据
        Converters._parse_to_xml(xml, json_data)
        
        xml.extend(['</dict>', '</plist>'])
        return '\n'.join(xml)
    
    @staticmethod
    def _parse_to_xml(xml: List[str], data: Any, indent: int = 1):
        """
        递归将JSON数据转换为XML
        
        Args:
            xml (list): XML字符串列表
            data (Any): 要转换的数据
            indent (int): 缩进级别
        """
        indent_str = '    ' * indent
        
        if isinstance(data, dict):
            for key, value in data.items():
                xml.append(f'{indent_str}<key>{key}</key>')
                
                if isinstance(value, dict):
                    # 处理特殊格式的对象
                    if key in ['frame', 'offset', 'sourceColorRect', 
                              'sourceSize', 'spriteSourceSize']:
                        Converters._parse_to_json(xml, value, indent)
                    else:
                        # 处理一般对象
                        xml.append(f'{indent_str}<dict>')
                        Converters._parse_to_xml(xml, value, indent + 1)
                        xml.append(f'{indent_str}</dict>')
                elif isinstance(value, list):
                    # 处理列表
                    xml.append(f'{indent_str}<array>')
                    for item in value:
                        if isinstance(item, dict):
                            xml.append(f'{indent_str}    <dict>')
                            Converters._parse_to_xml(xml, item, indent + 2)
                            xml.append(f'{indent_str}    </dict>')
                        else:
                            Converters._to_xml(xml, item, indent + 1)
                    xml.append(f'{indent_str}</array>')
                else:
                    # 处理基本类型值
                    Converters._to_xml(xml, value, indent)
        
    @staticmethod
    def _parse_to_json(xml: List[str], value: Dict[str, Any], indent: int):
        """
        将对象解析为特定格式的JSON字符串
        
        Args:
            xml (list): XML字符串列表
            value (dict): 值对象
            indent (int): 缩进级别
        """
        indent_str = '    ' * indent
        
        if 'x' in value and 'w' in value:
            # 包含位置和尺寸的对象
            json_str = f'{{{{{value["x"]},{value["y"]}}},{{{value["w"]},{value["h"]}}}}}'
        else:
            # 仅包含尺寸的对象
            json_str = f'{{{value["w"]},{value["h"]}}}'
        
        xml.append(f'{indent_str}<string>{json_str}</string>')
    
    @staticmethod
    def _to_xml(xml: List[str], value: Any, indent: int):
        """
        将基本类型的键值对写入XML
        
        Args:
            xml (list): XML字符串列表
            value (Any): 值
            indent (int): 缩进级别
        """
        indent_str = '    ' * indent
        
        if isinstance(value, bool):
            # 布尔值
            xml.append(f'{indent_str}<{str(value).lower()}/>')
        elif isinstance(value, int) or isinstance(value, float):
            # 数字
            xml.append(f'{indent_str}<integer>{value}</integer>')
        else:
            # 字符串或其他
            xml.append(f'{indent_str}<string>{value}</string>')
    
    @staticmethod
    def add_properties(json_data: Dict[str, Any], file_name: str) -> Dict[str, Any]:
        """
        添加必要的属性到JSON对象
        
        Args:
            json_data (dict): JSON对象
            file_name (str): 文件名
            
        Returns:
            dict: 增强后的JSON对象
        """
        # 创建元数据
        metadata = {
            "format": 3,
            "pixelFormat": "RGBA8888",
            "premultiplyAlpha": False,
            "realTextureFileName": f"{os.path.basename(file_name)}.png",
            "size": Converters.get_image_size(file_name),
            "smartupdate": f"$TexturePacker:SmartUpdate:{UuidUtils.generate_uuid()}:{UuidUtils.generate_uuid()}:{UuidUtils.generate_uuid()}$",
            "textureFileName": f"{os.path.basename(file_name)}.png"
        }
        
        # 将元数据添加到JSON
        result = {**json_data}
        result['metadata'] = metadata
        
        # 删除旧的元数据
        if 'meta' in result:
            del result['meta']
        
        return result
    
    @staticmethod
    def get_image_size(file_name: str) -> str:
        """
        获取图像尺寸
        
        Args:
            file_name (str): 文件名
            
        Returns:
            str: 格式化的尺寸字符串
        """
        try:
            from PIL import Image
            with Image.open(f"{file_name}.png") as img:
                width, height = img.size
            return f'{{{width},{height}}}'
        except Exception as e:
            logger()['exception'](f"读取图像文件 {file_name}.png 时出错", e)
            return '{0,0}'

class ResourceProcessor:
    """
    资源处理器类 - 参考Cocos Creator Web逆向工程实现
    """
    
    def __init__(self):
        # 数据存储
        self.file_list: List[str] = []
        self.file_map: Dict[str, str] = {}  # key: filename_without_ext, value: full_path
        self.cache_read_list: List[str] = []
        self.cache_write_list: List[str] = []
        self.node_data: Dict[str, Any] = {}
        
        # 资源映射
        self.scene_assets: List[Any] = []
        self.sprite_frames: Dict[str, Any] = {}
        self.audio_clips: List[Any] = []
        self.animations: List[Any] = []
        self.text_assets: List[Any] = []
        
        # 配置
        self.settings: Dict[str, Any] = {}
        self.paths: Dict[str, str] = {}
        self.file_manager: Optional[FileManager] = None
    
    def process_resources(self, paths: Dict[str, str], settings: Dict[str, Any], bundle_filter: str = None):
        """
        处理资源文件的主入口

        Args:
            paths (dict): 路径字典
            settings (dict): 全局设置
            bundle_filter (str, optional): 过滤bundle文件名的关键字，用于指定输出目录
        """
        logger()['info']("开始处理资源...")
        
        try:
            self.reset_state()
            self.paths = paths
            self.settings = settings
            self.bundle_filter = bundle_filter
            self.file_manager = FileManager(paths.get('output', ''), bundle_filter)
            
            # 保存资源根路径，用于计算相对路径
            self.res_root = paths.get('res', '')
            
            # 读取资源文件
            self.read_files(paths.get('res', ''), first=True)
            
            # 处理子包
            self.process_subpackages()
            
            # 解析bundle配置文件
            self.parse_bundle_config()
            
            # 过滤文件列表，只保留与指定bundle相关的文件
            if bundle_filter:
                self.filter_files_by_bundle(bundle_filter)
            
            # 处理JSON文件
            self.process_json_files()
            
            # 处理所有文件（包括非JSON文件）
            self.process_all_files()
            
            # 转换为输出文件
            self.convert_to_output_files()
            
            # 生成顶级目录的.meta文件
            self.generate_top_level_dir_metas()
            
            logger()['success']("资源处理完成")
        except Exception as e:
            logger()['exception']("处理资源文件时出错", e)
            raise
    
    def parse_bundle_config(self):
        """
        解析bundle配置文件，获取资源的原始路径和类型信息
        """
        logger()['info']("解析bundle配置文件...")
        
        # 查找所有config文件
        config_files = []
        for curr_path in self.file_list:
            if curr_path.endswith('.json'):
                filename = os.path.basename(curr_path)
                if filename.startswith('config.'):
                    config_files.append(curr_path)
        
        logger()['info'](f"找到 {len(config_files)} 个bundle配置文件")
        
        # 解析每个config文件
        self.bundle_configs = {}
        for config_path in config_files:
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 提取bundle名称
                bundle_name = os.path.splitext(os.path.basename(config_path))[0].replace('config.', '')
                
                # 保存bundle配置
                self.bundle_configs[bundle_name] = config_data
                
                logger()['debug'](f"解析bundle配置: {bundle_name}")
                
                # 提取资源映射信息
                if 'assets' in config_data:
                    self.asset_mappings = config_data['assets']
                    logger()['debug'](f"提取到 {len(self.asset_mappings)} 个资源映射")
                
            except Exception as e:
                logger()['exception'](f"解析bundle配置文件 {config_path} 时出错", e)
    
    def filter_files_by_bundle(self, bundle_filter: str):
        """
        根据bundle_filter过滤文件列表，只保留与指定bundle相关的文件
        
        Args:
            bundle_filter (str): bundle过滤关键字
        """
        # 检查资源根路径是否包含bundle_filter
        res_root = self.paths.get('res', '')
        is_bundle_specific_res = bundle_filter in res_root
        
        filtered_file_list = []
        filtered_file_relative_paths = {}
        
        for curr_path in self.file_list:
            relative_path = self.file_relative_paths.get(curr_path, '')
            
            # 情况1：资源根路径已经是特定bundle的路径
            if is_bundle_specific_res:
                # 保留所有文件，因为它们已经是特定bundle的资源
                filtered_file_list.append(curr_path)
                filtered_file_relative_paths[curr_path] = relative_path
                continue
            
            # 情况2：资源根路径包含所有bundle，需要根据相对路径过滤
            if relative_path:
                # 获取bundle名称（通常是相对路径的第一个目录）
                dir_parts = relative_path.split(os.sep)
                if len(dir_parts) > 0:
                    file_bundle = dir_parts[0]
                    # 如果文件属于指定bundle，则保留
                    if file_bundle == bundle_filter:
                        filtered_file_list.append(curr_path)
                        filtered_file_relative_paths[curr_path] = relative_path
            
        # 如果过滤后没有文件，可能是因为资源目录结构简单，没有bundle子目录
        # 这种情况通常发生在测试环境中，我们需要保留所有文件
        if not filtered_file_list:
            logger()['debug'](f"没有找到与bundle '{bundle_filter}' 相关的文件，保留所有文件")
            filtered_file_list = self.file_list
            filtered_file_relative_paths = self.file_relative_paths
        
        # 更新文件列表和相对路径字典
        self.file_list = filtered_file_list
        self.file_relative_paths = filtered_file_relative_paths
        
        logger()['info'](f"根据bundle过滤后，剩余 {len(filtered_file_list)} 个资源文件")
    
    def generate_top_level_dir_metas(self):
        """生成顶级目录的.meta文件"""
        # 分析所有处理过的目录，提取顶级目录
        top_level_dirs = set()
        
        # 从处理过的资源中提取目录信息
        for curr_path in self.file_list:
            relative_path = self.file_relative_paths.get(curr_path, '')
            if relative_path:
                # 获取顶级目录
                dir_parts = relative_path.split(os.sep)
                if len(dir_parts) > 1:
                    top_level_dir = dir_parts[0]
                    top_level_dirs.add(top_level_dir)
        
        # 为每个顶级目录生成.meta文件
        for dir_name in top_level_dirs:
            self.file_manager.write_directory_meta(dir_name)
    
    def processResources(self, paths: Dict[str, str], settings: Dict[str, Any] = None, bundle_filter: str = None):
        """
        兼容方法，支持reverseEngine.py的调用
        
        Args:
            paths (dict): 路径字典
            settings (dict, optional): 全局设置，默认None
            bundle_filter (str, optional): 过滤bundle文件名的关键字，用于指定输出目录
        """
        # 如果没有提供settings，使用空字典
        if settings is None:
            settings = {}
        
        return self.process_resources(paths, settings, bundle_filter)
    
    def reset_state(self):
        """重置处理器状态"""
        self.file_list = []
        self.file_map = {}
        self.cache_read_list = []
        self.cache_write_list = []
        self.node_data = {}
        self.scene_assets = []
        self.sprite_frames = {}
        self.audio_clips = []
        self.animations = []
        self.text_assets = []
        self.res_root = ""
        # 保存文件的相对路径信息
        self.file_relative_paths = {}  # key: full_path, value: relative_path
        # bundle配置信息
        self.bundle_configs = {}  # key: bundle_name, value: config_data
        self.asset_mappings = {}  # key: asset_uuid, value: asset_info
    
    def read_files(self, file_path: str, first: bool = False):
        """
        递归读取目录下所有文件
        
        Args:
            file_path (str): 文件路径
            first (bool): 是否为首次调用
        """
        try:
            if not os.path.exists(file_path):
                logger()['warn'](f"目录不存在: {file_path}")
                return
            
            for item in os.listdir(file_path):
                full_path = os.path.join(file_path, item)
                if os.path.isfile(full_path):
                    self.file_list.append(full_path)
                    # 保存相对路径
                    if self.res_root:
                        relative_path = os.path.relpath(full_path, self.res_root)
                        self.file_relative_paths[full_path] = relative_path
                    # 以文件名（不含扩展名）为key
                    filename_without_ext = os.path.splitext(item)[0]
                    self.file_map[filename_without_ext] = full_path
                else:
                    self.read_files(full_path, first=False)
            
            if first:
                logger()['info'](f"读取到 {len(self.file_list)} 个资源文件")
        except Exception as e:
            logger()['exception'](f"读取目录 {file_path} 时出错", e)
            raise
    
    def process_subpackages(self):
        """处理子包"""
        if self.settings and self.settings.get("subpackages"):
            subpackages_path = os.path.join(os.path.dirname(self.paths.get('res', '')), 'subpackages')
            if os.path.exists(subpackages_path):
                self.read_files(subpackages_path, first=False)
                logger()['debug'](f"处理子包: {subpackages_path}")
            else:
                logger()['warn'](f"子包路径不存在: {subpackages_path}")
    
    def process_json_files(self):
        """处理JSON文件"""
        for curr_path in self.file_list:
            if curr_path.endswith('.json'):
                try:
                    with open(curr_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    key = os.path.splitext(os.path.basename(curr_path))[0]
                    self.node_data = data
                    self.process_data(key, data)
                except Exception as e:
                    logger()['exception'](f"处理JSON文件 {curr_path} 时出错", e)
    
    def process_all_files(self):
        """
        处理所有文件，包括非JSON文件，生成逆向后的资源
        """
        logger()['info'](f"开始处理所有文件，共 {len(self.file_list)} 个文件")
        
        # 遍历所有文件
        for curr_path in self.file_list:
            # 跳过JSON文件，已经处理过了
            if curr_path.endswith('.json'):
                continue
            
            try:
                # 获取文件名和扩展名
                filename = os.path.basename(curr_path)
                ext = os.path.splitext(filename)[1].lower()
                basename = os.path.splitext(filename)[0]
                
                # 只处理需要逆向的资源类型，不执行任何复制操作
                if ext in ['.png', '.jpg', '.jpeg', '.mp3', '.wav', '.ogg', '.anim']:
                    # 获取相对路径，保持原有目录结构
                    relative_path = self.file_relative_paths.get(curr_path, filename)
                    
                    # 根据bundle配置文件获取资源的原始路径
                    original_path = relative_path
                    original_dir = os.path.dirname(original_path)
                    
                    # 如果有资源映射信息，尝试获取原始资源路径
                    if self.asset_mappings:
                        # 尝试根据文件名（不含扩展名）查找资源映射
                        asset_info = self.asset_mappings.get(basename, {})
                        if asset_info and isinstance(asset_info, dict):
                            # 获取原始资源路径
                            asset_path = asset_info.get('path', '')
                            if asset_path:
                                original_path = asset_path
                                original_dir = os.path.dirname(asset_path)
                                logger()['debug'](f"根据bundle配置文件获取到资源原始路径: {original_path}")
                    
                    # 生成唯一UUID
                    meta_uuid = UuidUtils.generate_uuid()
                    
                    # 生成meta数据
                    meta_data = {
                        "ver": "1.2.7",
                        "uuid": meta_uuid,
                        "optimizationPolicy": "AUTO",
                        "asyncLoadAssets": False,
                        "readonly": False,
                        "subMetas": {}
                    }
                    
                    # 写入.meta文件，使用原始目录结构
                    self.file_manager.write_file(original_dir, f"{filename}.meta", meta_data)
                    
                    # 根据文件类型确定资源类型
                    if ext in ['.png', '.jpg', '.jpeg']:
                        resource_type = "texture"
                    elif ext in ['.mp3', '.wav', '.ogg']:
                        resource_type = "audio"
                    elif ext == '.anim':
                        resource_type = "animation"
                    else:
                        resource_type = "other"
                    
                    logger()['info'](f"处理{resource_type}资源: {original_path} (uuid: {meta_uuid})")
                    
                    # 如果是动画文件，读取内容并写入，使用原始目录结构
                    if ext == '.anim':
                        with open(curr_path, 'r', encoding='utf-8') as f:
                            anim_data = json.load(f)
                        self.file_manager.write_file(original_dir, filename, anim_data)
                        self.animations.append(anim_data)
                else:
                    # 跳过不需要的文件类型（如编译后的js文件）
                    logger()['debug'](f"跳过不需要的文件类型: {curr_path}")
            except Exception as e:
                logger()['exception'](f"处理文件 {curr_path} 时出错", e)
    
    def process_data(self, key: str, data: Any):
        """
        处理数据
        
        Args:
            key (str): 键名
            data (Any): 要处理的数据
        """
        if not self.settings:
            logger()['warn']("全局设置为空，跳过数据处理")
            return
        
        processed_data = self.reveal_data(data)
        self.write_processed_data(processed_data, key)
    
    def reveal_data(self, json_object: Any) -> Any:
        """
        解析数据对象
        
        Args:
            json_object (Any): 要解析的JSON对象
        
        Returns:
            Any: 解析后的对象
        """
        # 这里可以添加数据解析逻辑
        return json_object
    
    def write_processed_data(self, data: Any, key: str):
        """
        写入处理后的数据
        
        Args:
            data (Any): 处理后的数据
            key (str): 键名
        """
        if isinstance(data, dict) and data.get("__type__"):
            self.process_type_data(data, key)
        else:
            for i, value in data.items():
                if isinstance(value, dict) and value.get('__type__'):
                    self.process_type_object(value.get('__type__'), data, i, key)
                elif isinstance(value, list):
                    # 处理列表类型
                    for item in value:
                        if isinstance(item, dict) and item.get('__type__'):
                            self.process_type_object(item.get('__type__'), value, i, key)
    
    def process_type_data(self, data: Dict[str, Any], key: str):
        """
        处理特定类型的数据
        
        Args:
            data (dict): 数据对象
            key (str): 键名
        """
        data_type = data.get("__type__")
        
        if data_type == "cc.AudioClip":
            self.process_audio_clip(data, key)
        elif data_type == "cc.TextAsset":
            self.process_text_asset(data, key)
        elif data_type == "cc.AnimationClip":
            self.process_animation_clip(data, key)
        elif data_type == "cc.SpriteFrame":
            self.process_sprite_frame_data(data, key)
        elif data_type == "cc.Texture2D":
            self.process_texture_2d(data, key)
        elif data_type == "cc.Prefab":
            self.process_prefab(data, key)
        else:
            logger()['debug'](f"未处理的数据类型: {data_type}")
    
    def process_type_object(self, type_name: str, data: Any, index: str, key: str):
        """
        处理特定类型的对象
        
        Args:
            type_name (str): 对象类型
            data (Any): 数据对象
            index (str): 索引
            key (str): 键名
        """
        if type_name == 'cc.SceneAsset':
            self.process_scene_asset(data, index, key)
        elif type_name == 'cc.SpriteFrame':
            self.process_sprite_frame(data, index, key)
        else:
            logger()['debug'](f"未处理的对象类型: {type_name}")
    
    def process_audio_clip(self, data: Dict[str, Any], key: str):
        """
        处理音频资源

        Args:
            data (dict): 音频数据
            key (str): 键名
        """
        native_file = data.get('_native', '')
        if not native_file:
            logger()['warn'](f"音频资源缺少_native字段: {key}")
            return

        # 获取音频文件名
        name = os.path.basename(native_file)
        
        # 获取原始路径
        original_dir = ""
        
        # 首先尝试从bundle配置文件中获取原始路径
        if self.asset_mappings:
            asset_info = self.asset_mappings.get(key, {})
            if asset_info and isinstance(asset_info, dict):
                asset_path = asset_info.get('path', '')
                if asset_path:
                    original_dir = os.path.dirname(asset_path)
                    logger()['debug'](f"根据bundle配置文件获取到音频资源原始路径: {asset_path}")
        
        # 如果bundle配置文件中没有，查找对应的JSON文件获取原有路径
        if not original_dir:
            json_file_path = next((path for path in self.file_list if path.endswith(f'{key}.json')), None)
            if json_file_path:
                # 获取相对路径，保持原有目录结构
                relative_path = self.file_relative_paths.get(json_file_path, '')
                original_dir = os.path.dirname(relative_path)
        
        meta_uuid = key

        meta_data = {
            "ver": "1.2.7",
            "uuid": meta_uuid,
            "optimizationPolicy": "AUTO",
            "asyncLoadAssets": False,
            "readonly": False,
            "subMetas": {}
        }

        # 写入.meta文件，使用原始目录结构
        self.file_manager.write_file(original_dir, f"{name}.meta", meta_data)
        self.audio_clips.append(data)
        
        # 记录日志，包含完整路径
        if original_dir:
            logger()['info'](f"处理音频资源: {os.path.join(original_dir, name)} (uuid: {meta_uuid})")
        else:
            logger()['info'](f"处理音频资源: {name} (uuid: {meta_uuid})")
    
    def process_text_asset(self, data: Dict[str, Any], key: str):
        """
        处理文本资源

        Args:
            data (dict): 文本数据
            key (str): 键名
        """
        # 获取文本名称
        name = data.get('_name', '') or f"text_{key}"
        if not name.endswith('.json'):
            name += '.json'
        
        # 查找对应的JSON文件，获取原有路径
        json_file_path = next((path for path in self.file_list if path.endswith(f'{key}.json')), None)
        dir_part = ""
        if json_file_path:
            # 获取相对路径，保持原有目录结构
            relative_path = self.file_relative_paths.get(json_file_path, '')
            dir_part = os.path.dirname(relative_path)
        
        meta_uuid = key

        meta_data = {
            "ver": "1.2.7",
            "uuid": meta_uuid,
            "asyncLoadAssets": False,
            "subMetas": {}
        }

        # 写入资源文件和meta文件，保持原有目录结构
        self.file_manager.write_file(dir_part, name, data)
        self.file_manager.write_file(dir_part, f"{name}.meta", meta_data)
        self.text_assets.append(data)
        
        # 记录日志，包含完整路径
        if dir_part:
            logger()['info'](f"处理文本资源: {os.path.join(dir_part, name)}")
        else:
            logger()['info'](f"处理文本资源: {name}")
    
    def process_animation_clip(self, data: Dict[str, Any], key: str):
        """
        处理动画资源

        Args:
            data (dict): 动画数据
            key (str): 键名
        """
        # 获取动画名称
        name = data.get('_name', '') or f"animation_{key}"
        
        # 添加.anim扩展名
        if not name.endswith('.anim'):
            name += '.anim'
        
        # 获取原始路径
        original_dir = ""
        
        # 首先尝试从bundle配置文件中获取原始路径
        if self.asset_mappings:
            asset_info = self.asset_mappings.get(key, {})
            if asset_info and isinstance(asset_info, dict):
                asset_path = asset_info.get('path', '')
                if asset_path:
                    original_dir = os.path.dirname(asset_path)
                    logger()['debug'](f"根据bundle配置文件获取到动画资源原始路径: {asset_path}")
        
        # 如果bundle配置文件中没有，查找对应的JSON文件获取原有路径
        if not original_dir:
            json_file_path = next((path for path in self.file_list if path.endswith(f'{key}.json')), None)
            if json_file_path:
                # 获取相对路径，保持原有目录结构
                relative_path = self.file_relative_paths.get(json_file_path, '')
                original_dir = os.path.dirname(relative_path)
        
        filename = name
        meta_uuid = key
        
        # 写入动画文件，使用原始目录结构
        self.file_manager.write_file(original_dir, filename, data)
        self.animations.append(data)
        
        meta_data = {
            "ver": "1.2.7",
            "uuid": meta_uuid,
            "optimizationPolicy": "AUTO",
            "asyncLoadAssets": False,
            "readonly": False,
            "subMetas": {}
        }
        
        # 写入.meta文件，使用原始目录结构
        self.file_manager.write_file(original_dir, f"{filename}.meta", meta_data)
        
        # 记录日志，包含完整路径
        if original_dir:
            logger()['info'](f"处理动画资源: {os.path.join(original_dir, name)}")
        else:
            logger()['info'](f"处理动画资源: {name}")
    
    def process_scene_asset(self, data: Any, index: str, key: str):
        """
        处理场景资源
        
        Args:
            data (Any): 场景数据
            index (str): 索引
            key (str): 键名
        """
        if isinstance(data, list) and len(data) > 0:
            scene_name = data[0].get('_name', 'Scene')
        else:
            scene_name = "Scene"
        
        filename = f"{scene_name}.fire"
        mkdir = "Scene"
        
        # 写入场景文件
        self.file_manager.write_file(mkdir, filename, data)
        self.scene_assets.append(json.dumps(data))
        
        # 查找匹配的node数据并生成meta文件
        for node_key, node_value in self.node_data.items():
            if isinstance(node_value, list) and len(node_value) > 0:
                node_name = node_value[0].get('_name', '')
                if node_name == scene_name:
                    # 生成UUID
                    meta_uuid = self.create_library(node_key, key)
                    meta_data = {
                        "ver": "1.2.7",
                        "uuid": meta_uuid,
                        "optimizationPolicy": "AUTO",
                        "asyncLoadAssets": False,
                        "readonly": False,
                        "subMetas": {}
                    }
                    # 写入.meta文件
                    self.file_manager.write_file(mkdir, f"{filename}.meta", meta_data)
                    break
        
        logger()['info'](f"处理场景资源: {scene_name}")
    
    def process_sprite_frame(self, data: Any, index: str, key: str):
        """
        处理精灵帧资源
        
        Args:
            data (Any): 精灵帧数据
            index (str): 索引
            key (str): 键名
        """
        self.sprite_frames[key] = data
        logger()['debug'](f"处理精灵帧资源: {key}")
    
    def process_sprite_frame_data(self, data: Dict[str, Any], key: str):
        """
        处理精灵帧数据

        Args:
            data (dict): 精灵帧数据
            key (str): 键名
        """
        name = data.get('_name', '') or f"sprite_frame_{key}"
        
        # 添加.plist扩展名
        if not name.endswith('.plist'):
            name += '.plist'
        
        # 查找对应的JSON文件，获取原有路径
        json_file_path = next((path for path in self.file_list if path.endswith(f'{key}.json')), None)
        dir_part = ""
        if json_file_path:
            # 获取相对路径，保持原有目录结构
            relative_path = self.file_relative_paths.get(json_file_path, '')
            dir_part = os.path.dirname(relative_path)
        
        meta_uuid = key

        # 生成精灵帧meta数据
        meta_data = {
            "ver": "1.2.7",
            "uuid": meta_uuid,
            "optimizationPolicy": "AUTO",
            "asyncLoadAssets": False,
            "readonly": False,
            "subMetas": {}
        }

        # 写入精灵帧文件，保持原有目录结构
        self.file_manager.write_file(dir_part, f"{name}", {})
        self.file_manager.write_file(dir_part, f"{name}.meta", meta_data)

        self.sprite_frames[key] = data
        
        # 记录日志，包含完整路径
        if dir_part:
            logger()['info'](f"处理精灵帧数据: {os.path.join(dir_part, name)}")
        else:
            logger()['info'](f"处理精灵帧数据: {name}")
    
    def process_texture_2d(self, data: Dict[str, Any], key: str):
        """
        处理纹理资源

        Args:
            data (dict): 纹理数据
            key (str): 键名
        """
        # 获取纹理名称和原生文件路径
        name = data.get('_name', '') or f"texture_{key}"
        _native = data.get('_native', '')
        
        # 如果有原生文件路径，使用其扩展名
        if _native:
            ext = os.path.splitext(_native)[1]
            name = name + ext
        
        # 查找对应的JSON文件，获取原有路径
        json_file_path = next((path for path in self.file_list if path.endswith(f'{key}.json')), None)
        dir_part = ""
        if json_file_path:
            # 获取相对路径，保持原有目录结构
            relative_path = self.file_relative_paths.get(json_file_path, '')
            dir_part = os.path.dirname(relative_path)
        
        meta_uuid = key

        # 生成纹理meta数据
        meta_data = {
            "ver": "1.2.7",
            "uuid": meta_uuid,
            "optimizationPolicy": "AUTO",
            "asyncLoadAssets": False,
            "readonly": False,
            "subMetas": {}
        }

        # 写入纹理数据文件，保持原有目录结构
        self.file_manager.write_file(dir_part, f"{name}.json", data)
        
        # 写入meta文件，保持原有目录结构
        self.file_manager.write_file(dir_part, f"{name}.meta", meta_data)
        
        # 记录日志，包含完整路径
        if dir_part:
            logger()['info'](f"处理纹理资源: {os.path.join(dir_part, name)}")
        else:
            logger()['info'](f"处理纹理资源: {name}")
    
    def process_prefab(self, data: Dict[str, Any], key: str):
        """
        处理预制体资源

        Args:
            data (dict): 预制体数据
            key (str): 键名
        """
        # 获取预制体名称
        name = data.get('_name', '') or f"prefab_{key}"
        
        # 添加.prefab扩展名
        if not name.endswith('.prefab'):
            name += '.prefab'
        
        # 查找对应的JSON文件，获取原有路径
        json_file_path = next((path for path in self.file_list if path.endswith(f'{key}.json')), None)
        dir_part = ""
        if json_file_path:
            # 获取相对路径，保持原有目录结构
            relative_path = self.file_relative_paths.get(json_file_path, '')
            dir_part = os.path.dirname(relative_path)
        
        meta_uuid = key

        # 生成预制体meta数据
        meta_data = {
            "ver": "1.2.7",
            "uuid": meta_uuid,
            "optimizationPolicy": "AUTO",
            "asyncLoadAssets": False,
            "readonly": False,
            "subMetas": {}
        }

        # 写入预制体文件，保持原有目录结构
        self.file_manager.write_file(dir_part, name, data)
        
        # 写入.meta文件，保持原有目录结构
        self.file_manager.write_file(dir_part, f"{name}.meta", meta_data)
        
        # 记录日志，包含完整路径
        if dir_part:
            logger()['info'](f"处理预制体资源: {os.path.join(dir_part, name)}")
        else:
            logger()['info'](f"处理预制体资源: {name}")
    
    def create_library(self, index: str, key: str) -> str:
        """
        创建库
        
        Args:
            index (str): 索引
            key (str): 键名
        
        Returns:
            str: 生成的UUID
        """
        if self.settings and self.settings.get('uuids'):
            return self.settings['uuids'].get(key, UuidUtils.generate_uuid())
        return UuidUtils.generate_uuid()
    
    def convert_to_output_files(self):
        """
        转换为输出文件
        """
        # 不执行任何复制操作，只处理资源转换
        logger()['info']("不执行任何文件复制操作")
        
        # 转换特殊资源
        Converters.convert_sprite_atlas(self.sprite_frames)
        
        logger()['info'](f"处理了 0 个资源文件（不执行复制操作）")
    
    def copy_files(self):
        """
        复制文件到输出目录
        """
        try:
            for i in range(len(self.cache_read_list)):
                source_path = self.cache_read_list[i]
                target_path = self.cache_write_list[i]
                
                # 确保目标目录存在
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                
                # 复制文件
                shutil.copy2(source_path, target_path)
                logger()['debug'](f"复制文件: {os.path.basename(source_path)} -> {target_path}")
        except Exception as e:
            logger()['exception']("复制文件时出错", e)
            raise
    
    def getResourceStats(self):
        """
        获取资源处理统计信息
        
        Returns:
            dict: 资源统计信息
        """
        return {
            'total': len(self.file_list),
            'audio': len(self.audio_clips),
            'text': len(self.text_assets),
            'animation': len(self.animations),
            'scene': len(self.scene_assets),
            'sprite_frame': len(self.sprite_frames),
            'processed': len(self.cache_read_list)
        }

# 创建全局实例
resourceProcessor = ResourceProcessor()
