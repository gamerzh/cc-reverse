#!/usr/bin/env python3
"""
日志工具
"""

import time
from rich.console import Console
from rich.theme import Theme
from rich.traceback import install

# 安装rich的回溯处理
install()

# 自定义主题
custom_theme = Theme({
    "info": "cyan",
    "error": "bold red",
    "success": "bold green",
    "warn": "yellow",
    "debug": "magenta",
    "timestamp": "dim"
})

console = Console(theme=custom_theme)

class Logger:
    """日志类"""
    
    # 日志级别
    LEVELS = {
        "debug": 0,
        "info": 1,
        "warn": 2,
        "error": 3,
        "success": 4
    }
    
    def __init__(self):
        """初始化"""
        self.level = "info"  # 默认日志级别
        self.show_timestamp = True  # 是否显示时间戳
        self.verbose = False  # 是否显示详细信息
    
    def set_level(self, level):
        """设置日志级别
        
        Args:
            level (str): 日志级别，可选值：debug, info, warn, error, success
        """
        if level in self.LEVELS:
            self.level = level
    
    def set_verbose(self, verbose):
        """设置是否显示详细信息
        
        Args:
            verbose (bool): 是否显示详细信息
        """
        self.verbose = verbose
    
    def _should_log(self, message_level):
        """判断是否应该记录该级别的日志
        
        Args:
            message_level (str): 消息的日志级别
        
        Returns:
            bool: 是否应该记录
        """
        return self.LEVELS.get(message_level, 0) >= self.LEVELS.get(self.level, 0)
    
    def _format_message(self, level, message, **kwargs):
        """格式化消息
        
        Args:
            level (str): 日志级别
            message (str): 日志消息
            **kwargs: 额外参数
        
        Returns:
            str: 格式化后的消息
        """
        parts = []
        
        # 添加时间戳
        if self.show_timestamp:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            parts.append(f"[timestamp][{timestamp}][/timestamp]")
        
        # 添加日志级别
        parts.append(f"[{level}]")
        
        # 添加消息
        parts.append(message)
        
        # 添加额外信息
        if self.verbose and kwargs:
            extra_info = " ".join([f"{k}={v}" for k, v in kwargs.items()])
            parts.append(f" {extra_info}")
        
        return " ".join(parts)
    
    def info(self, message, **kwargs):
        """信息日志"""
        if self._should_log("info"):
            console.print(self._format_message("info", message, **kwargs))
    
    def error(self, message, **kwargs):
        """错误日志"""
        if self._should_log("error"):
            console.print(self._format_message("error", message, **kwargs))
    
    def success(self, message, **kwargs):
        """成功日志"""
        if self._should_log("success"):
            console.print(self._format_message("success", message, **kwargs))
    
    def warn(self, message, **kwargs):
        """警告日志"""
        if self._should_log("warn"):
            console.print(self._format_message("warn", message, **kwargs))
    
    def debug(self, message, **kwargs):
        """调试日志"""
        if self._should_log("debug"):
            console.print(self._format_message("debug", message, **kwargs))
    
    def exception(self, message, ex):
        """异常日志"""
        if self._should_log("error"):
            console.print(self._format_message("error", f"{message}: {str(ex)}"))
            # 打印异常回溯
            if self.verbose:
                import traceback
                console.print(f"[error]{traceback.format_exc()}[/error]")

# 创建全局日志实例
logger_instance = Logger()

def logger():
    """获取日志实例"""
    return logger_instance
