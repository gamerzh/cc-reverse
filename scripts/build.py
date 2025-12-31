#!/usr/bin/env python3
"""
构建脚本
"""

import os
import shutil
import subprocess
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

# 构建目录
BUILD_DIR = os.path.join(os.path.dirname(__file__), '../dist')
PKG_PATH = os.path.join(os.path.dirname(__file__), '../package.json')


def clean_dir(dir_path):
    """
    清理目录
    
    Args:
        dir_path (str): 要清理的目录
    """
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.makedirs(dir_path, exist_ok=True)


def copy_file(src, dest):
    """
    复制文件
    
    Args:
        src (str): 源文件
        dest (str): 目标文件
    """
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(src, dest)


def copy_dir(src, dest):
    """
    复制目录
    
    Args:
        src (str): 源目录
        dest (str): 目标目录
    """
    # 确保目标目录存在
    os.makedirs(dest, exist_ok=True)
    
    # 复制目录内容
    for item in os.listdir(src):
        src_path = os.path.join(src, item)
        dest_path = os.path.join(dest, item)
        
        if os.path.isdir(src_path):
            # 递归复制子目录
            copy_dir(src_path, dest_path)
        else:
            # 复制文件
            copy_file(src_path, dest_path)


def build():
    """
    构建项目
    """
    console.print("[info]开始构建项目...[/info]")
    
    try:
        # 1. 清理构建目录
        console.print("[info]清理构建目录...[/info]")
        clean_dir(BUILD_DIR)
        
        # 2. 复制源文件
        console.print("[info]复制源文件...[/info]")
        copy_dir(os.path.join(os.path.dirname(__file__), '../src'), os.path.join(BUILD_DIR, 'src'))
        copy_dir(os.path.join(os.path.dirname(__file__), '../cc_reverse'), os.path.join(BUILD_DIR, 'cc_reverse'))
        copy_dir(os.path.join(os.path.dirname(__file__), '../bin'), os.path.join(BUILD_DIR, 'bin'))
        
        # 3. 复制配置文件
        console.print("[info]复制配置文件...[/info]")
        copy_file(os.path.join(os.path.dirname(__file__), '../setup.py'), os.path.join(BUILD_DIR, 'setup.py'))
        copy_file(os.path.join(os.path.dirname(__file__), '../README.md'), os.path.join(BUILD_DIR, 'README.md'))
        copy_file(os.path.join(os.path.dirname(__file__), '../README_PYTHON.md'), os.path.join(BUILD_DIR, 'README_PYTHON.md'))
        copy_file(os.path.join(os.path.dirname(__file__), '../cc-reverse.config.js'), 
                 os.path.join(BUILD_DIR, 'cc-reverse.config.json'))
        
        # 4. 设置执行权限
        console.print("[info]设置执行权限...[/info]")
        bin_path = os.path.join(BUILD_DIR, 'bin/cc-reverse')
        # 在Windows上设置执行权限可能需要特殊处理，这里跳过
        
        # 5. 安装依赖
        console.print("[info]安装依赖...[/info]")
        os.chdir(BUILD_DIR)
        subprocess.run(['pip', 'install', '-e', '.'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 6. 完成构建
        console.print("[success]项目构建完成！[/success]")
        console.print(f"\n构建目录: [cyan]{BUILD_DIR}[/cyan]")
        console.print(f"\n安装: [yellow]pip install -g {BUILD_DIR}[/yellow]")
        console.print(f"运行: [yellow]cc-reverse --path <源项目路径>[/yellow]")
        
    except Exception as e:
        console.print(f"[error]构建失败: {e}[/error]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    import sys
    build()
