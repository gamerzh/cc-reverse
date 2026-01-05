#!/usr/bin/env python3
"""
Bundle提取器 - 将编译后的bundle文件拆分为原始模块
支持将提取的模块保存到对应的bundle文件夹下
"""

import re
import os
import sys
import argparse
from pathlib import Path

def find_module_object(content):
    """查找模块映射对象的位置"""
    # 查找 window.__require=function 的位置
    marker = 'window.__require=function'
    start_idx = content.find(marker)
    if start_idx == -1:
        return None
    
    # 找到函数体开始的 '{'
    func_brace_start = content.find('{', start_idx)
    if func_brace_start == -1:
        return None
    
    # 使用栈平衡找到函数体结束的 '}'
    brace_count = 1
    pos = func_brace_start + 1
    in_string = False
    string_char = None
    escape = False
    
    while pos < len(content):
        c = content[pos]
        
        if escape:
            escape = False
        elif c == '\\':
            escape = True
        elif not in_string:
            if c in ('"', "'"):
                in_string = True
                string_char = c
            elif c == '{':
                brace_count += 1
            elif c == '}':
                brace_count -= 1
                if brace_count == 0:
                    func_brace_end = pos
                    break
        elif c == string_char:
            in_string = False
        
        pos += 1
    
    # 在函数体结束后查找 '(' 和 '{'
    # 模式是 ...}({...})
    # 找到下一个 '('
    paren_start = content.find('(', func_brace_end)
    if paren_start == -1:
        return None
    
    # 找到对象开始的 '{'
    obj_brace_start = content.find('{', paren_start)
    if obj_brace_start == -1:
        return None
    
    # 使用栈平衡找到对象结束的 '}'
    brace_count = 1
    pos = obj_brace_start + 1
    in_string = False
    string_char = None
    escape = False
    
    while pos < len(content):
        c = content[pos]
        
        if escape:
            escape = False
        elif c == '\\':
            escape = True
        elif not in_string:
            if c in ('"', "'"):
                in_string = True
                string_char = c
            elif c == '{':
                brace_count += 1
            elif c == '}':
                brace_count -= 1
                if brace_count == 0:
                    obj_brace_end = pos
                    return obj_brace_start, obj_brace_end + 1
        elif c == string_char:
            in_string = False
        
        pos += 1
    
    return None

def extract_modules(content, start, end):
    """从对象内容中提取模块"""
    obj_content = content[start:end]
    
    modules = []
    pos = 1  # 跳过开头的 '{'
    
    while pos < len(obj_content):
        # 跳过空白
        while pos < len(obj_content) and obj_content[pos].isspace():
            pos += 1
        
        if pos >= len(obj_content) or obj_content[pos] == '}':
            break
        
        # 解析键
        if obj_content[pos] == '"':
            # 双引号字符串
            key_start = pos + 1
            pos += 1
            while pos < len(obj_content) and obj_content[pos] != '"':
                if obj_content[pos] == '\\':
                    pos += 1
                pos += 1
            if pos >= len(obj_content):
                break
            key = obj_content[key_start:pos]
            pos += 1  # 跳过 closing '"'
        else:
            # 标识符（可能没有引号）
            key_start = pos
            while pos < len(obj_content) and obj_content[pos] not in (':', ' ', '\t', '\n', '\r'):
                pos += 1
            key = obj_content[key_start:pos]
        
        # 跳过到 ':'
        while pos < len(obj_content) and obj_content[pos] != ':':
            pos += 1
        if pos >= len(obj_content):
            break
        pos += 1  # 跳过 ':'
        
        # 跳过空白
        while pos < len(obj_content) and obj_content[pos].isspace():
            pos += 1
        
        if pos >= len(obj_content):
            break
        
        # 现在应该是 '['
        if obj_content[pos] != '[':
            # 不是数组，跳过这个值
            # 简单跳过直到逗号或}
            while pos < len(obj_content) and obj_content[pos] not in (',', '}'):
                pos += 1
            if pos < len(obj_content) and obj_content[pos] == ',':
                pos += 1
            continue
        
        # 开始解析数组
        pos += 1  # 跳过 '['
        
        # 跳过空白
        while pos < len(obj_content) and obj_content[pos].isspace():
            pos += 1
        
        if pos >= len(obj_content):
            break
        
        # 第一个元素应该是 function
        if not obj_content.startswith('function', pos):
            # 不是函数，跳过整个数组
            brace_count = 0
            while pos < len(obj_content):
                c = obj_content[pos]
                if c == '[' or c == '{':
                    brace_count += 1
                elif c == ']' or c == '}':
                    brace_count -= 1
                    if c == ']' and brace_count == 0:
                        pos += 1
                        break
                pos += 1
            continue
        
        # 提取函数
        func_start = pos
        # 找到函数体结束
        brace_count = 0
        in_func = False
        
        while pos < len(obj_content):
            c = obj_content[pos]
            
            if c == '{':
                brace_count += 1
                if obj_content[pos-1] == ')':
                    in_func = True
            elif c == '}':
                brace_count -= 1
                if in_func and brace_count == 0:
                    func_end = pos
                    pos += 1
                    break
            
            pos += 1
        
        function_code = obj_content[func_start:func_end+1]
        
        # 跳过逗号
        while pos < len(obj_content) and (obj_content[pos].isspace() or obj_content[pos] == ','):
            pos += 1
        
        # 第二个元素应该是依赖对象
        if pos >= len(obj_content) or obj_content[pos] != '{':
            # 没有依赖对象，跳过到数组结束
            while pos < len(obj_content) and obj_content[pos] != ']':
                pos += 1
            if pos < len(obj_content):
                pos += 1
            continue
        
        # 提取依赖对象
        dep_start = pos
        brace_count = 0
        
        while pos < len(obj_content):
            c = obj_content[pos]
            
            if c == '{':
                brace_count += 1
            elif c == '}':
                brace_count -= 1
                if brace_count == 0:
                    dep_end = pos
                    pos += 1
                    break
            
            pos += 1
        
        deps = obj_content[dep_start:dep_end+1]
        
        # 跳过到 ']'
        while pos < len(obj_content) and obj_content[pos] != ']':
            pos += 1
        if pos < len(obj_content):
            pos += 1
        
        # 添加到模块列表
        modules.append((key, function_code, deps))
        
        # 跳过逗号或空白
        while pos < len(obj_content) and (obj_content[pos].isspace() or obj_content[pos] == ','):
            pos += 1
    
    return modules

def save_modules(modules, output_dir, bundle_name):
    """保存模块到指定目录"""
    os.makedirs(output_dir, exist_ok=True)
    
    saved_count = 0
    for name, code, deps in modules:
        # 清理模块名，确保是安全的文件名
        safe_name = re.sub(r'[\\/*?:"<>|]', '_', name)
        
        # 创建输出文件路径
        output_path = os.path.join(output_dir, f"{safe_name}.js")
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # 写入模块信息
                f.write(f"// 模块: {name}\n")
                f.write(f"// 来自bundle: {bundle_name}\n")
                f.write(f"// 依赖: {deps}\n\n")
                f.write(code)
            
            saved_count += 1
        except Exception as e:
            print(f"保存模块 {name} 时出错: {e}")
    
    return saved_count

def extract_bundle(input_file, output_base_dir=None):
    """
    提取bundle文件中的模块
    
    Args:
        input_file: 输入的bundle文件路径
        output_base_dir: 输出基础目录，如果为None则使用bundle所在目录
    
    Returns:
        tuple: (成功提取的模块数, 输出目录)
    """
    print(f"处理bundle文件: {input_file}")
    
    # 读取文件
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"读取文件失败: {e}")
        return 0, None
    
    print(f"文件大小: {len(content)} 字节")
    
    # 查找模块对象
    result = find_module_object(content)
    if not result:
        print("未找到模块对象")
        return 0, None
    
    start, end = result
    print(f"模块对象范围: {start} - {end}")
    print(f"对象大小: {end - start} 字节")
    
    # 提取模块
    modules = extract_modules(content, start, end)
    print(f"找到 {len(modules)} 个模块")
    
    if not modules:
        print("没有提取到模块")
        return 0, None
    
    # 确定输出目录
    input_path = Path(input_file)
    bundle_name = input_path.parent.name  # 例如 'fhpoker'
    
    if output_base_dir:
        # 检查output_base_dir是否已经以bundle_name结尾
        if os.path.basename(output_base_dir) == bundle_name:
            # 如果已经以bundle_name结尾，直接创建script子目录
            output_dir = os.path.join(output_base_dir, "script")
        else:
            # 否则创建bundle_name/script子目录
            output_dir = os.path.join(output_base_dir, bundle_name, "script")
    else:
        # 否则在bundle所在目录下创建script子目录
        output_dir = input_path.parent / "script"
        output_dir = str(output_dir)
    
    print(f"输出目录: {output_dir}")
    
    # 保存模块
    saved_count = save_modules(modules, output_dir, bundle_name)
    print(f"成功保存 {saved_count} 个模块到 {output_dir}")
    
    # 显示前几个模块的信息
    print("\n前5个模块:")
    for i, (name, code, deps) in enumerate(modules[:5]):
        print(f"  {i+1}. {name} (代码长度: {len(code)})")
    
    return saved_count, output_dir

def main():
    parser = argparse.ArgumentParser(description='提取Cocos bundle Creator文件中的模块')
    parser.add_argument('input', help='输入的bundle文件路径')
    parser.add_argument('-o', '--output', help='输出目录（可选），默认在bundle文件同目录下')
    parser.add_argument('--list', action='store_true', help='只列出模块，不保存')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"错误: 文件不存在: {args.input}")
        sys.exit(1)
    
    # 提取模块
    saved_count, output_dir = extract_bundle(args.input, args.output)
    
    if saved_count > 0:
        print(f"\n完成! 共提取 {saved_count} 个模块到 {output_dir}")
    else:
        print("\n未提取到任何模块")

if __name__ == "__main__":
    main()