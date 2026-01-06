#!/usr/bin/env python3
"""
调试脚本：测试混合架构工作流
"""

import os
import subprocess
import sys

def is_node_available():
    """检查Node.js是否可用"""
    try:
        # 使用PowerShell兼容的语法
        result = subprocess.run(
            "node --version", 
            shell=True, 
            capture_output=True, 
            text=True, 
            encoding='utf-8'
        )
        return result.returncode == 0
    except Exception:
        return False

def run_test():
    """运行测试"""
    print("开始测试混合架构工作流...")
    
    # 检查Node.js是否可用
    if not is_node_available():
        print("\nNode.js不可用，跳过测试")
        print("请安装Node.js后再运行测试")
        return
    
    # 1. 安装js_analyzer依赖
    print("\n1. 安装js_analyzer依赖...")
    # 使用PowerShell执行npm命令
    subprocess.run(
        "npm install", 
        shell=True, 
        cwd="js_analyzer", 
        check=True, 
        encoding='utf-8'
    )
    
    # 2. 运行js_analyzer解析代码
    print("\n2. 运行js_analyzer解析代码...")
    # 使用PowerShell执行node命令
    subprocess.run(
        f"node parse_bundle.js ..\\debug\\test_sample.js ..\\output", 
        shell=True, 
        cwd="js_analyzer", 
        check=True, 
        encoding='utf-8'
    )
    
    # 3. 运行py_generator生成代码
    print("\n3. 运行py_generator生成代码...")
    subprocess.run([
        "python", "py_generator/gen_ts.py", 
        "output/test_sample.js.json", 
        "output/generated_code",
        "--format", "typescript"
    ], check=True)
    
    # 4. 显示结果
    print("\n4. 显示生成的文件...")
    generated_files = []
    for root, dirs, files in os.walk("output/generated_code"):
        for file in files:
            generated_files.append(os.path.join(root, file))
    
    if generated_files:
        print(f"生成了 {len(generated_files)} 个文件：")
        for file in generated_files:
            print(f"  - {file}")
            
            # 显示文件内容前500字符
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"    内容（前500字符）:")
                print("    " + "="*40)
                print(content[:500] + ("..." if len(content) > 500 else ""))
                print("    " + "="*40)
    else:
        print("未生成任何文件！")
    
    print("\n测试完成！")

if __name__ == "__main__":
    run_test()
