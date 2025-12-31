#!/usr/bin/env python3
"""
配置加载器
"""

import os
import json

def loadConfig():
    """
    加载配置文件
    
    Returns:
        dict: 配置字典
    """
    config = {
        # 默认配置
        "output": {
            "createMeta": True,
            "prettify": True,
            "includeComments": True
        },
        "codeGen": {
            "language": "typescript",
            "moduleType": "commonjs",
            "indentSize": 2,
            "indent": "space"
        },
        "assets": {
            "extractTextures": True,
            "extractAudio": True,
            "extractAnimations": True,
            "optimizeSprites": False
        }
    }
    
    # 检查项目根目录的配置文件
    config_path = os.path.join(os.getcwd(), "cc-reverse.config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            # 合并用户配置到默认配置
            config = mergeConfig(config, user_config)
        except Exception as e:
            from src.utils.logger import logger
            logger().warn(f"加载配置文件失败: {e}")
    
    return config

def mergeConfig(default_config, user_config):
    """
    合并配置字典
    
    Args:
        default_config (dict): 默认配置
        user_config (dict): 用户配置
    
    Returns:
        dict: 合并后的配置
    """
    for key, value in user_config.items():
        if key in default_config and isinstance(default_config[key], dict) and isinstance(value, dict):
            # 递归合并字典
            default_config[key] = mergeConfig(default_config[key], value)
        else:
            # 直接替换值
            default_config[key] = value
    
    return default_config
