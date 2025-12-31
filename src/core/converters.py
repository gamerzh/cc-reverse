#!/usr/bin/env python3
"""
资源格式转换工具
"""

import os
import json
import uuid
import xml.etree.ElementTree as ET
from PIL import Image
from src.utils.logger import logger
from src.utils.fileManager import fileManager

class Converters:
    """资源格式转换工具类"""
    
    def convertSpriteAtlas(self, spriteFrames):
        """
        转换精灵图集
        
        Args:
            spriteFrames (dict): 精灵帧对象
        """
        try:
            # 转换逻辑
            logger().info('处理精灵图集...')
        except Exception as e:
            logger().error(f'转换精灵图集时出错: {e}')
    
    def jsonToPlist(self, fileName):
        """
        将 JSON 转换为 PLIST 格式
        
        Args:
            fileName (str): 文件名（不含扩展名）
        """
        try:
            # 读取 JSON 文件
            with open(f'{fileName}.json', 'r', encoding='utf-8') as f:
                data = f.read()
            
            json_data = json.loads(data)
            
            # 添加必要的属性
            enhanced_json = self.addProperties(json_data, fileName)
            
            # 创建 XML 文档
            xml_content = self.createXmlDocument(enhanced_json)
            
            # 写入 PLIST 文件
            fileManager.writeFile(f'{fileName}.plist', xml_content)
            
            logger().debug(f'转换完成: {fileName}.json -> {fileName}.plist')
        except Exception as e:
            logger().error(f'转换文件 {fileName} 时出错: {e}')
    
    def createXmlDocument(self, json_data):
        """
        创建 XML 文档
        
        Args:
            json_data (dict): JSON 对象
        
        Returns:
            str: XML 文档内容
        """
        # 创建根元素
        plist = ET.Element('plist')
        plist.set('version', '1.0')
        
        # 创建 doctype
        doctype = '<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
        
        # 创建主字典
        root_dict = ET.SubElement(plist, 'dict')
        self.parsetoXML(root_dict, json_data)
        
        # 生成 XML 字符串
        xml_str = ET.tostring(plist, encoding='utf-8', method='xml')
        
        # 组合完整的 XML 文档
        xml_content = f'<?xml version="1.0" encoding="UTF-8"?>{doctype}\n{xml_str.decode("utf-8")}'
        
        return xml_content
    
    def parsetoXML(self, parent, json_data):
        """
        将 JSON 对象解析为 XML
        
        Args:
            parent (xml.etree.ElementTree.Element): 父元素
            json_data (dict): JSON 对象
        """
        for key, value in json_data.items():
            # 写入键
            key_elem = ET.SubElement(parent, 'key')
            key_elem.text = key
            
            if isinstance(value, dict):
                # 处理特殊格式的对象
                if key in ['frame', 'offset', 'sourceColorRect', 'sourceSize', 'spriteSourceSize']:
                    self.parsetoJson(parent, value)
                else:
                    # 处理一般对象
                    dict_elem = ET.SubElement(parent, 'dict')
                    self.parsetoXML(dict_elem, value)
            elif isinstance(value, list):
                # 处理数组
                array_elem = ET.SubElement(parent, 'array')
                for item in value:
                    if isinstance(item, dict):
                        item_dict = ET.SubElement(array_elem, 'dict')
                        self.parsetoXML(item_dict, item)
                    else:
                        # 简单类型
                        self.toXML(array_elem, '', item)
            else:
                # 处理基本类型值
                self.toXML(parent, '', value)
    
    def toXML(self, parent, key, value):
        """
        将基本类型的键值对写入 XML
        
        Args:
            parent (xml.etree.ElementTree.Element): 父元素
            key (str): 键
            value: 值
        """
        # 写入值
        if isinstance(value, bool):
            # 布尔值
            bool_elem = ET.SubElement(parent, str(value).lower())
        elif isinstance(value, int) or isinstance(value, float):
            # 数字
            integer_elem = ET.SubElement(parent, 'integer')
            integer_elem.text = str(int(value))
        else:
            # 字符串或其他
            string_elem = ET.SubElement(parent, 'string')
            string_elem.text = str(value)
    
    def parsetoJson(self, parent, value):
        """
        将对象解析为特定格式的 JSON 字符串
        
        Args:
            parent (xml.etree.ElementTree.Element): 父元素
            value (dict): 值对象
        """
        string_elem = ET.SubElement(parent, 'string')
        
        if 'x' in value and 'w' in value:
            # 包含位置和尺寸的对象
            json_str = f'{{{{{value["x"]},{value["y"]}}},{{{value["w"]},{value["h"]}}}}}'
        else:
            # 仅包含尺寸的对象
            json_str = f'{{{value["w"]},{value["h"]}}}'
        
        string_elem.text = json_str
    
    def addProperties(self, json_data, fileName):
        """
        添加必要的属性到 JSON 对象
        
        Args:
            json_data (dict): JSON 对象
            fileName (str): 文件名
        
        Returns:
            dict: 增强后的 JSON 对象
        """
        # 创建元数据
        metadata = {
            'format': 3,
            'pixelFormat': 'RGBA8888',
            'premultiplyAlpha': False,
            'realTextureFileName': f'{os.path.basename(fileName)}.png',
            'size': self.getImageSize(fileName),
            'smartupdate': f'$TexturePacker:SmartUpdate:{uuid.uuid4()}:{uuid.uuid4()}:{uuid.uuid4()}$',
            'textureFileName': f'{os.path.basename(fileName)}.png'
        }
        
        # 将元数据添加到 JSON
        result = json_data.copy()
        result['metadata'] = metadata
        
        # 删除旧的元数据
        if 'meta' in result:
            del result['meta']
        
        return result
    
    def getImageSize(self, fileName):
        """
        获取图像尺寸
        
        Args:
            fileName (str): 文件名
        
        Returns:
            str: 格式化的尺寸字符串
        """
        try:
            # 使用 PIL 获取图像尺寸
            with Image.open(f'{fileName}.png') as img:
                width, height = img.size
            return f'{{{width},{height}}}'
        except Exception as e:
            logger().error(f'读取图像文件 {fileName}.png 时出错: {e}')
            return '{0,0}'

# 创建全局实例
converters = Converters()
