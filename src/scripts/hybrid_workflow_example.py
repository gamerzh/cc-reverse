#!/usr/bin/env python3
"""
混合架构工作流示例

展示如何使用Node.js + Python的混合架构处理代码：
1. 使用Node.js分析JavaScript代码，生成中间JSON
2. 使用Python从JSON生成最终代码
"""

import os
import subprocess
import sys

def run_node_analyzer(input_path, output_json):
    """运行Node.js代码分析器
    
    Args:
        input_path: 输入文件或目录
        output_json: 输出JSON文件
    
    Returns:
        bool: 是否成功
    """
    print("=" * 60)
    print("1. 运行Node.js代码分析器")
    print("=" * 60)
    
    # 检查Node.js是否安装
    if not is_node_installed():
        print("错误: Node.js未安装")
        return False
    
    # 检查npm依赖是否安装
    if not is_npm_deps_installed():
        print("安装npm依赖...")
        if not install_npm_deps():
            print("错误: 安装npm依赖失败")
            return False
    
    # 构建Node.js命令
    node_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools', 'node_js_analyzer.js')
    command = f"node {node_script} {input_path} {output_json}"
    
    print(f"运行命令: {command}")
    
    # 执行命令（指定UTF-8编码避免解码错误）
    result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
    
    print(f"退出码: {result.returncode}")
    print(f"标准输出: {result.stdout}")
    if result.stderr:
        print(f"标准错误: {result.stderr}")
    
    return result.returncode == 0

def run_python_generator(json_path, output_dir, output_format='javascript'):
    """运行Python代码生成器
    
    Args:
        json_path: 中间JSON文件
        output_dir: 输出目录
        output_format: 输出格式
    
    Returns:
        bool: 是否成功
    """
    print("\n" + "=" * 60)
    print("2. 运行Python代码生成器")
    print("=" * 60)
    
    # 构建Python命令
    python_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools', 'json_based_generator.py')
    command = f"python {python_script} {json_path} {output_dir} --format {output_format}"
    
    print(f"运行命令: {command}")
    
    # 执行命令（指定UTF-8编码避免解码错误）
    result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
    
    print(f"退出码: {result.returncode}")
    print(f"标准输出: {result.stdout}")
    if result.stderr:
        print(f"标准错误: {result.stderr}")
    
    return result.returncode == 0

def is_node_installed():
    """检查Node.js是否安装
    
    Returns:
        bool: 是否安装
    """
    try:
        result = subprocess.run("node --version", shell=True, capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def is_npm_deps_installed():
    """检查npm依赖是否安装
    
    Returns:
        bool: 是否安装
    """
    # 检查node_modules目录是否存在
    node_modules_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'node_modules')
    return os.path.exists(node_modules_path)

def install_npm_deps():
    """安装npm依赖
    
    Returns:
        bool: 是否成功
    """
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    command = f"cd {project_root} && npm install"
    
    print(f"运行命令: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    print(f"退出码: {result.returncode}")
    print(f"标准输出: {result.stdout}")
    if result.stderr:
        print(f"标准错误: {result.stderr}")
    
    return result.returncode == 0

def main():
    """主函数"""
    print("混合架构工作流示例")
    print("=" * 60)
    
    # 获取脚本目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    
    # 示例输入输出路径（使用测试文件）
    input_path = os.path.join(project_root, 'test_sample.js')
    output_json = os.path.join(project_root, 'output', 'analysis_result.json')
    output_dir = os.path.join(project_root, 'output', 'generated_code')
    output_format = 'javascript'  # 或 'typescript'
    
    # 创建输出目录
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 运行Node.js分析器
    if not run_node_analyzer(input_path, output_json):
        print("\n错误: Node.js分析器运行失败")
        sys.exit(1)
    
    # 2. 运行Python生成器
    if not run_python_generator(output_json, output_dir, output_format):
        print("\n错误: Python生成器运行失败")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("工作流完成！")
    print(f"中间JSON: {output_json}")
    print(f"生成代码目录: {output_dir}")
    print("=" * 60)

if __name__ == '__main__':
    main()