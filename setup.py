#!/usr/bin/env python3
"""
Cocos Creator 逆向工程工具
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cc-reverse",
    version="1.0.0",
    author="",
    author_email="",
    description="Cocos Creator 逆向工程工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Crain99/cc-reverse",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "colorama",
        "rich",
        "tqdm",
        "filetype",
        "pillow",
        "click",
    ],
    entry_points={
        "console_scripts": [
            "cc-reverse=reverse.main:cli",
        ],
    },
)
