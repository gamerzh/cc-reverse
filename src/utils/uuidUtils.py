#!/usr/bin/env python3
"""
UUID 工具类
"""

import random
import base64
import string
from src.utils.logger import logger

# Base64 编码映射表
BASE64_KEYS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='

# 创建 Base64 值映射字典
BASE64_VALUES = {}
for i in range(123):
    BASE64_VALUES[i] = 64  # 填充占位符('=')索引
for i in range(64):
    BASE64_VALUES[ord(BASE64_KEYS[i])] = i

# 十六进制字符列表
HEX_CHARS = list('0123456789abcdef')

# UUID 模板构建
_t = ['', '', '', '']
UUID_TEMPLATE = _t + _t + ['-'] + _t + ['-'] + _t + ['-'] + _t + ['-'] + _t + _t + _t
INDICES = [i for i, x in enumerate(UUID_TEMPLATE) if x != '-']

class UuidUtils:
    """UUID 工具类"""
    
    def generateUuid(self):
        """
        生成随机 UUID
        
        Returns:
            str: 随机 UUID
        """
        return ''.join(random.choices(string.ascii_letters + string.digits, k=22))
    
    def decodeUuid(self, base64_str):
        """
        将 Base64 编码的 UUID 转换为标准 UUID 格式
        示例: fcmR3XADNLgJ1ByKhqcC5Z -> fc991dd7-0033-4b80-9d41-c8a86a702e59
        
        Args:
            base64_str (str): Base64 编码的 UUID
        
        Returns:
            str: 标准格式的 UUID
        """
        # 参数检查
        if not isinstance(base64_str, str):
            logger().warn("解码 UUID 失败: 输入必须是字符串")
            return None
        
        # 长度检查
        if len(base64_str) != 22:
            # 如果不是标准长度的 Base64 UUID，直接返回原值
            return base64_str
        
        try:
            # 创建模板副本
            uuid_template = UUID_TEMPLATE.copy()
            
            # 填充模板的前两个字符
            uuid_template[0] = base64_str[0]
            uuid_template[1] = base64_str[1]
            
            # 解码剩余字符
            j = 0
            for i in range(2, 22, 2):
                lhs = BASE64_VALUES[ord(base64_str[i])]
                rhs = BASE64_VALUES[ord(base64_str[i + 1])]
                
                uuid_template[INDICES[j]] = HEX_CHARS[lhs >> 2]
                j += 1
                uuid_template[INDICES[j]] = HEX_CHARS[((lhs & 3) << 2) | (rhs >> 4)]
                j += 1
                uuid_template[INDICES[j]] = HEX_CHARS[rhs & 0xF]
                j += 1
            
            # 返回标准 UUID
            return ''.join(uuid_template)
        except Exception as e:
            logger().error(f"解码 UUID 时出错: {e}")
            return base64_str  # 出错时返回原始值
    
    def compress_uuid(self, uuid_str):
        """
        压缩 UUID (23位)
        将标准的 UUID 转换为压缩的 23 位格式
        
        Args:
            uuid_str (str): 标准 UUID
        
        Returns:
            str: 压缩后的 UUID
        """
        try:
            # 分离 UUID 前缀和内容
            header = uuid_str[:5]
            content = uuid_str[5:].replace('-', '') + 'f'
            
            # 转换内容为字节数组
            byte_array = []
            for i in range(0, len(content) - 1, 2):
                byte_array.append(int(content[i:i+2], 16))
            
            # 转换为 Base64 并返回结果
            base64_content = base64.b64encode(bytes(byte_array)).decode('utf-8')
            return header + base64_content[:-2]
        except Exception as e:
            logger().error(f"压缩 UUID 时出错: {e}")
            return uuid_str  # 出错时返回原始值
    
    def decompress_uuid(self, uuid_str):
        """
        解压缩 UUID (22位)
        将 22 位格式的 UUID 转换为标准格式
        
        Args:
            uuid_str (str): 22位 UUID
        
        Returns:
            str: 解压缩后的 UUID
        """
        try:
            # 分离 UUID 前缀和内容
            header = uuid_str[:2]
            content = uuid_str[2:].replace('-', '') + 'f'
            
            # 转换内容为字节数组
            byte_array = []
            for i in range(0, len(content) - 1, 2):
                byte_array.append(int(content[i:i+2], 16))
            
            # 转换为 Base64 并返回结果
            base64_content = base64.b64encode(bytes(byte_array)).decode('utf-8')
            return header + base64_content
        except Exception as e:
            logger().error(f"解压缩 UUID 时出错: {e}")
            return uuid_str  # 出错时返回原始值
    
    def original_uuid(self, uuid_str):
        """
        将 23 位 UUID 转换为 22 位格式
        
        Args:
            uuid_str (str): 23位 UUID
        
        Returns:
            str: 22位 UUID
        """
        try:
            # 转换成长的 UUID
            header = uuid_str[:5]
            end = uuid_str[5:]
            
            # 处理 Base64 填充
            temp = end
            if len(end) % 3 == 1:
                temp += "=="
            elif len(end) % 3 == 2:
                temp += "="
            
            # 转换为十六进制
            base64_content = base64.b64decode(temp).hex()
            long_uuid = header + base64_content
            
            # 返回转换后的 UUID
            result = self.decompress_uuid(long_uuid)[:4] + end
            return result
        except Exception as e:
            logger().error(f"转换 UUID 格式时出错: {e}")
            return uuid_str  # 出错时返回原始值

# 创建全局实例
uuidUtils = UuidUtils()
