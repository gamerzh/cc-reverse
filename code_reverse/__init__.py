#!/usr/bin/env python3
"""
code_reverse - 代码逆向模块
"""

import os
import json
import subprocess
import shutil
from pathlib import Path
from .py_generator.gen_ts import TypeScriptGenerator

class CodeReverse:
    """代码逆向主类"""
    
    def __init__(self, config=None):
        """初始化代码逆向模块
        
        Args:
            config: 配置选项
        """
        self.config = config or {
            'output_format': 'typescript',
            'temp_dir': 'temp',
            'scripts_dir': 'assets/scripts',
            'preserve_temp': False
        }
        self.ts_generator = TypeScriptGenerator()
        self.js_analyzer_path = os.path.join(os.path.dirname(__file__), 'js_analyzer')
        self.js_deps_installed = False
    
    def analyze_code(self, input_path, output_path, file_patterns=['*.js', '*.jsbundle'], bundle_filter=None):
        """
        分析代码，生成中间JSON
        
        Args:
            input_path: 输入文件或目录
            output_path: 输出目录
            file_patterns: 要处理的文件模式列表
            bundle_filter: 过滤bundle文件名的关键字，用于指定要处理的特定bundle
            
        Returns:
            bool: 是否成功
        """
        print(f"使用JS分析器分析代码: {input_path} -> {output_path}")
        
        # 确保输出目录存在
        os.makedirs(output_path, exist_ok=True)
        
        # 运行JS分析器
        js_analyzer_script = os.path.join(self.js_analyzer_path, 'parse_bundle.js')
        
        # 安装依赖
        if not self.js_deps_installed:
            self._install_js_dependencies()
            self.js_deps_installed = True
        
        # 收集要处理的文件
        files_to_process = []
        if os.path.isfile(input_path):
            # 单个文件
            # 检查是否符合bundle_filter条件
            if bundle_filter:
                if bundle_filter.lower() in input_path.lower():
                    files_to_process = [input_path]
            else:
                files_to_process = [input_path]
        else:
            # 目录，根据文件模式收集文件
            for pattern in file_patterns:
                import glob
                pattern_path = os.path.join(input_path, '**', pattern)
                files = glob.glob(pattern_path, recursive=True)
                
                # 如果指定了bundle_filter，只保留包含该关键字的文件
                if bundle_filter:
                    filtered_files = [f for f in files if bundle_filter.lower() in f.lower()]
                    files_to_process.extend(filtered_files)
                    print(f"模式 {pattern} 匹配到 {len(files)} 个文件，过滤后保留 {len(filtered_files)} 个文件")
                else:
                    files_to_process.extend(files)
                    print(f"模式 {pattern} 匹配到 {len(files)} 个文件")
        
        # 去重
        files_to_process = list(set(files_to_process))
        
        print(f"最终找到 {len(files_to_process)} 个文件需要处理")
        
        all_success = True
        
        # 处理每个文件
        for file_path in files_to_process:
            print(f"处理文件: {file_path}")
            
            # 构建命令
            cmd = [
                'node',
                js_analyzer_script,
                file_path,
                output_path
            ]
            
            # 运行命令
            result = subprocess.run(
                cmd,
                cwd=self.js_analyzer_path,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            # 打印输出
            if result.stdout:
                print("JS分析器输出:")
                print(result.stdout)
            
            if result.stderr:
                print("JS分析器错误:")
                print(result.stderr)
            
            if result.returncode != 0:
                print(f"JS分析器运行失败，返回码: {result.returncode}")
                all_success = False
        
        return all_success
    
    def generate_code(self, json_path, output_dir, output_format=None):
        """
        从JSON生成代码
        
        Args:
            json_path: JSON文件或目录
            output_dir: 输出目录
            output_format: 输出格式 (javascript/typescript)
            
        Returns:
            bool: 是否成功
        """
        # 使用配置的默认格式或传入的格式
        format_ = output_format or self.config['output_format']
        print(f"从JSON生成代码: {json_path} -> {output_dir} ({format_})")
        
        # 使用Python生成器
        try:
            if os.path.isdir(json_path):
                self.ts_generator.generate_from_dir(json_path, output_dir, format_)
            else:
                self.ts_generator.generate_from_json(json_path, output_dir, format_)
            return True
        except Exception as e:
            print(f"代码生成失败: {str(e)}")
            return False
    
    def _install_js_dependencies(self):
        """安装JS分析器的依赖"""
        package_json = os.path.join(self.js_analyzer_path, 'package.json')
        node_modules = os.path.join(self.js_analyzer_path, 'node_modules')
        
        # 检查依赖是否已安装
        if not os.path.exists(node_modules):
            print("安装JS分析器依赖...")
            
            cmd = ['npm', 'install']
            result = subprocess.run(
                cmd,
                cwd=self.js_analyzer_path,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode != 0:
                print(f"依赖安装失败: {result.stderr}")
            else:
                print("依赖安装成功")
        else:
            print("JS分析器依赖已安装")
    
    def reverse_code(self, input_path, output_dir, output_format=None):
        """
        完整的代码逆向流程
        
        Args:
            input_path: 输入文件或目录
            output_dir: 输出目录
            output_format: 输出格式 (javascript/typescript)
            
        Returns:
            bool: 是否成功
        """
        print(f"开始完整的代码逆向流程: {input_path} -> {output_dir}")
        
        # 创建临时目录
        temp_dir = os.path.join(output_dir, self.config['temp_dir'])
        os.makedirs(temp_dir, exist_ok=True)
        
        # 1. 分析代码，生成中间JSON
        json_output = os.path.join(temp_dir, 'json')
        if not self.analyze_code(input_path, json_output):
            print("代码分析失败")
            return False
        
        # 2. 从JSON生成代码
        code_output = os.path.join(output_dir, self.config['scripts_dir'])
        if not self.generate_code(json_output, code_output, output_format):
            print("代码生成失败")
            return False
        
        # 3. 清理临时文件
        if not self.config['preserve_temp']:
            print("清理临时文件...")
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        print(f"代码逆向完成: {input_path} -> {output_dir}")
        return True
    
    def get_supported_formats(self):
        """
        获取支持的输出格式
        
        Returns:
            list: 支持的格式列表
        """
        return ['typescript', 'javascript']
    
    def set_config(self, key, value):
        """
        设置配置选项
        
        Args:
            key: 配置键
            value: 配置值
        """
        self.config[key] = value
    
    def get_config(self, key, default=None):
        """
        获取配置选项
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        return self.config.get(key, default)

# 创建全局实例
code_reverse = CodeReverse()

# 导出便捷函数
def reverse_code(input_path, output_dir, output_format='typescript'):
    """
    便捷函数：完整的代码逆向流程
    
    Args:
        input_path: 输入文件或目录
        output_dir: 输出目录
        output_format: 输出格式 (javascript/typescript)
        
    Returns:
        bool: 是否成功
    """
    return code_reverse.reverse_code(input_path, output_dir, output_format)

def analyze_code(input_path, output_path):
    """
    便捷函数：分析代码，生成中间JSON
    
    Args:
        input_path: 输入文件或目录
        output_path: 输出目录
        
    Returns:
        bool: 是否成功
    """
    return code_reverse.analyze_code(input_path, output_path)

def generate_code(json_path, output_dir, output_format='typescript'):
    """
    便捷函数：从JSON生成代码
    
    Args:
        json_path: JSON文件或目录
        output_dir: 输出目录
        output_format: 输出格式 (javascript/typescript)
        
    Returns:
        bool: 是否成功
    """
    return code_reverse.generate_code(json_path, output_dir, output_format)