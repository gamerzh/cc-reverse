#!/usr/bin/env python3
"""
Setup.py for Cocos Creator Reverse Engineering Tool
"""

from setuptools import setup, find_packages
import os

# 读取README.md文件
with open(os.path.join(os.path.dirname(__file__), 'README.md'), 'r', encoding='utf-8') as f:
    long_description = f.read()

# 读取requirements.txt文件
with open(os.path.join(os.path.dirname(__file__), 'requirements.txt'), 'r', encoding='utf-8') as f:
    requirements = f.read().splitlines()

setup(
    # 项目基本信息
    name="cc-reverse",
    version="0.1.1",
    description="Cocos Creator 逆向工程工具，用于将Web编译输出转换回可编辑的Cocos Creator项目",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/cc-reverse",
    license="MIT",
    
    # 项目分类
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Reverse Engineering",
        "Topic :: Games/Entertainment",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    
    # 关键字
    keywords="cocos-creator reverse-engineering game-development javascript typescript",
    
    # Python版本要求
    python_requires=">=3.7",
    
    # 依赖列表
    install_requires=requirements,
    
    # 项目结构
    packages=find_packages(exclude=['debug', 'test*']),
    include_package_data=True,
    
    # 入口点（命令行工具）
    entry_points={
        'console_scripts': [
            'cc-reverse=main.main:cli',
        ],
    },
    
    # 额外的URL
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/cc-reverse/issues',
        'Source': 'https://github.com/yourusername/cc-reverse',
        'Documentation': 'https://github.com/yourusername/cc-reverse#readme',
    },
    
    # 数据文件
    data_files=[
        ('', ['README.md', 'requirements.txt', '.gitignore']),
    ],
)
