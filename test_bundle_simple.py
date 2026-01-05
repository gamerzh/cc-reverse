#!/usr/bin/env python3
"""
简单bundle解析器 - 使用正则表达式提取模块
"""

import re
import os
import json

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
    
    # 使用正则表达式匹配模块定义
    # 模式: "模块名": [function(...){...}, {...}]
    # 简化：先匹配键值对，然后解析值
    
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

def main():
    file_path = r"C:\Workflow\xsh5\build\web-mobile\assets\fhpoker\index.f3dcd.js"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"文件大小: {len(content)} 字节")
    
    # 查找模块对象
    result = find_module_object(content)
    if not result:
        print("未找到模块对象")
        return
    
    start, end = result
    print(f"模块对象范围: {start} - {end}")
    print(f"对象大小: {end - start} 字节")
    
    # 提取模块
    modules = extract_modules(content, start, end)
    print(f"找到 {len(modules)} 个模块")
    
    # 显示前几个模块
    for i, (name, code, deps) in enumerate(modules[:5]):
        print(f"\n模块 {i+1}: {name}")
        print(f"代码长度: {len(code)}")
        print(f"代码前200字符: {code[:200]}...")
        print(f"依赖: {deps[:100]}...")
    
    # 保存模块
    output_dir = "extracted_fhpoker"
    os.makedirs(output_dir, exist_ok=True)
    
    for name, code, deps in modules:
        safe_name = re.sub(r'[\\/*?:"<>|]', '_', name)
        output_path = os.path.join(output_dir, f"{safe_name}.js")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"// 模块: {name}\n")
            f.write(f"// 依赖: {deps}\n\n")
            f.write(code)
        
        print(f"保存: {name} -> {output_path}")
    
    print(f"\n总计保存了 {len(modules)} 个模块")

if __name__ == "__main__":
    main()