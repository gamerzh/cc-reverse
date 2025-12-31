#!/usr/bin/env python3
"""
Cocos Creator 逆向工程工具主入口
"""

import os
import sys
import click
from rich.console import Console
from rich.theme import Theme

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

# 导入核心模块
from core.reverseEngine import reverseProject

# 自定义主题
custom_theme = Theme({
    "info": "cyan",
    "error": "bold red",
    "success": "bold green",
    "warn": "yellow",
    "debug": "magenta"
})

console = Console(theme=custom_theme)

def logger():
    """日志工具"""
    return {
        "info": console.print,
        "error": lambda x: console.print(f"[error]{x}[/error]"),
        "success": lambda x: console.print(f"[success]{x}[/success]"),
        "warn": lambda x: console.print(f"[warn]{x}[/warn]"),
        "debug": lambda x: console.print(f"[debug]{x}[/debug]")
    }

@click.command()
@click.version_option("1.0.0")
@click.option("-p", "--path", type=click.Path(exists=True), help="源项目路径")
@click.option("-o", "--output", type=str, default="./output", help="输出路径")
@click.option("-v", "--verbose", is_flag=True, default=False, help="显示详细日志")
@click.option("-s", "--silent", is_flag=True, default=False, help="静默模式，不显示进度")
@click.option("--version-hint", type=str, default="", help="提示Cocos Creator版本 (2.3.x|2.4.x)")
def cli(path, output, verbose, silent, version_hint):
    """Cocos Creator 逆向工程工具"""
    
    # 获取源路径
    source_path = path or os.environ.get("CC_SOURCE_PATH")
    if not source_path:
        logger()["error"]("错误: 未指定源路径，请通过命令行参数 --path 或环境变量 CC_SOURCE_PATH 指定")
        logger()["info"]("用法: python -m reverse.main --path <源项目路径>")
        sys.exit(1)
    
    # 设置输出目录：不指定时默认使用本工程的output目录
    if output == "./output":
        # 获取本工程的目录
        project_dir = os.path.dirname(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        output = os.path.join(project_dir, "output")
    
    # 开始逆向工程过程
    try:
        logger()["info"]("开始处理项目...")
        
        # 调用核心逆向工程函数
        reverseProject({
            "sourcePath": os.path.abspath(source_path),
            "outputPath": os.path.abspath(output),
            "verbose": verbose,
            "silent": silent,
            "versionHint": version_hint
        })
        
        logger()["success"]("逆向工程完成！")
    except Exception as e:
        logger()["error"](f"处理过程中出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    cli()
