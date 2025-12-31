#!/usr/bin/env python3
"""
日志工具
"""

from rich.console import Console
from rich.theme import Theme

# 自定义主题
custom_theme = Theme({
    "info": "cyan",
    "error": "bold red",
    "success": "bold green",
    "warn": "yellow",
    "debug": "magenta"
})

console = Console(theme=custom_theme)

class Logger:
    """日志类"""
    
    def info(self, message):
        """信息日志"""
        console.print(f"[info]{message}[/info]")
    
    def error(self, message):
        """错误日志"""
        console.print(f"[error]{message}[/error]")
    
    def success(self, message):
        """成功日志"""
        console.print(f"[success]{message}[/success]")
    
    def warn(self, message):
        """警告日志"""
        console.print(f"[warn]{message}[/warn]")
    
    def debug(self, message):
        """调试日志"""
        console.print(f"[debug]{message}[/debug]")

# 创建全局日志实例
logger_instance = Logger()

def logger():
    """获取日志实例"""
    return logger_instance
