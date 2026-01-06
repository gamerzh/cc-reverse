#!/usr/bin/env python3
"""
模块转换器 - 将Webpack模块函数转换为可读的TypeScript格式
"""

import re
import os
import json
import ast
import sys
from pathlib import Path

try:
    import esprima
    ESPRIMA_AVAILABLE = True
except ImportError:
    ESPRIMA_AVAILABLE = False
    print("警告: esprima模块未安装，将使用正则表达式回退分析")

class ModuleConverter:
    """Webpack模块转换器"""
    
    def __init__(self):
        self.converted_modules = []
    
    def extract_inner_code(self, webpack_code):
        """
        从Webpack模块函数中提取内部代码
        
        格式: function(e,t,o){"use strict";cc._RF.push(...); ...}
        """
        if not webpack_code.strip():
            return webpack_code
        
        # 尝试提取函数体内容
        # 查找 function(...){ 和对应的 }
        func_match = re.match(r'function\s*\([^)]*\)\s*\{([\s\S]*)\}', webpack_code)
        if func_match:
            inner_code = func_match.group(1)
            # 移除开头的"use strict";（如果存在）
            inner_code = re.sub(r'^"use strict";', '', inner_code.strip())
            return inner_code
        
        # 如果不是function格式，直接返回
        return webpack_code
    
    def extract_class_name(self, code):
        """从代码中提取类名"""
        # 方法1: 从cc._RF.push中提取
        rf_pattern = r'cc\._RF\.push\([^,]+,\s*"[^"]+",\s*"([^"]+)"\)'
        rf_match = re.search(rf_pattern, code)
        if rf_match:
            return rf_match.group(1)
        
        # 方法2: 从导出中提取
        export_patterns = [
            r'o\.(\w+)\s*=',
            r't\.exports\s*=\s*(\w+)',
            r'module\.exports\s*=\s*(\w+)'
        ]
        
        for pattern in export_patterns:
            export_match = re.search(pattern, code)
            if export_match:
                return export_match.group(1)
        
        return None
    
    def extract_export_mapping(self, code):
        """提取导出映射关系 o.ClassName = variableName"""
        # 模式: o.ClassName = variableName
        export_patterns = [
            r'o\.(\w+)\s*=\s*(\w+)',
            r't\.exports\s*=\s*(\w+)',
            r'module\.exports\s*=\s*(\w+)',
            r'exports\.(\w+)\s*=\s*(\w+)',
            r'\b(\w+)\s*=\s*(\w+)\s*;?\s*(?:,|$)'
        ]
        
        mappings = {}
        for pattern in export_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                if len(match.groups()) >= 2:
                    export_name = match.group(1)
                    var_name = match.group(2)
                    mappings[var_name] = export_name
        
        return mappings
    
    def extract_decorator_mapping(self, code):
        """提取装饰器变量到实际装饰器的映射"""
        # 模式: var s = cc._decorator.ccclass
        # 模式: var p = cc._decorator.property
        decorator_patterns = [
            r'var\s+(\w+)\s*=\s*cc\._decorator\.(\w+)',
            r'let\s+(\w+)\s*=\s*cc\._decorator\.(\w+)',
            r'const\s+(\w+)\s*=\s*cc\._decorator\.(\w+)',
            r'(\w+)\s*=\s*cc\._decorator\.(\w+)',
        ]
        
        mappings = {}
        for pattern in decorator_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                if len(match.groups()) >= 2:
                    var_name = match.group(1)
                    decorator_name = match.group(2)
                    mappings[var_name] = decorator_name
        
        return mappings
    
    def find_cc_class_definitions(self, code):
        """查找cc.Class定义"""
        class_patterns = [
            r'cc\.Class\s*\(\s*\{([\s\S]*?)\}\s*\)',
            r'\w\.Class\s*\(\s*\{([\s\S]*?)\}\s*\)',
            r'\w\["Class"\]\s*\(\s*\{([\s\S]*?)\}\s*\)',
            r"\w\['Class'\]\s*\(\s*\{([\s\S]*?)\}\s*\)",
            r'\.Class\s*\(\s*\{([\s\S]*?)\}\s*\)',
        ]
        
        class_definitions = []
        for pattern in class_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                class_body = match.group(1)
                class_definitions.append({
                    'start': match.start(),
                    'end': match.end(),
                    'body': class_body,
                    'full_match': match.group(0),
                    'type': 'cc_class'
                })
        
        # 查找TypeScript装饰器类
        ts_class_definitions = self.find_typescript_class_definitions(code)
        class_definitions.extend(ts_class_definitions)
        
        return class_definitions
    
    def find_typescript_class_definitions(self, code):
        """查找TypeScript装饰器类定义"""
        ts_classes = []
        
        # 模式1：查找装饰器应用模式: (i|r)([decorator], className)}(parentClass)
        # 这是TypeScript装饰器应用的标准模式，装饰器函数可能是i或r
        pattern1 = r'(i|r)\(\[([^\]]+)\],\s*(\w+)\)\}\(([^)]+)\)'
        
        matches1 = re.finditer(pattern1, code)
        for match in matches1:
            decorator_func = match.group(1)  # i或r
            decorators = match.group(2)
            class_name = match.group(3)
            parent_class = match.group(4)
            
            # 获取匹配的结束位置
            match_end = match.end()
            
            # 向后查找对应的函数定义
            # 我们需要找到 function(parentParam) { ... } 部分
            # 从match.start()向前搜索，最多搜索2000个字符
            search_start = max(0, match.start() - 2000)
            search_text = code[search_start:match.start()]
            
            # 查找类定义函数
            # 模式: (var className = )?function(parentParam) { function className() { ... } ... }
            func_pattern = r'(?:var\s+(\w+)\s*=\s*)?function\s*\((\w+)\)\s*\{[^}]*?function\s+' + re.escape(class_name) + r'[^}]*?\}'
            func_match = re.search(func_pattern, search_text)
            
            if func_match:
                class_var = func_match.group(1)
                parent_param = func_match.group(2)
                
                # 找到整个类定义的开始
                class_start = search_start + func_match.start()
                class_end = match.end()
                
                # 提取完整的类定义
                class_full = code[class_start:class_end]
                
                class_info = {
                    'start': class_start,
                    'end': class_end,
                    'full_match': class_full,
                    'type': 'typescript_class',
                    'class_var': class_var,
                    'class_name': class_name,
                    'decorators': decorators,
                    'parent_class': parent_class,
                    'parent_param': parent_param,
                    'body': class_full  # 整个类定义作为body
                }
                
                ts_classes.append(class_info)
            else:
                # 如果没找到完整的函数定义，至少记录装饰器信息
                class_info = {
                    'start': match.start(),
                    'end': match.end(),
                    'full_match': match.group(0),
                    'type': 'typescript_class',
                    'class_name': class_name,
                    'decorators': decorators,
                    'parent_class': parent_class,
                    'body': ''
                }
                ts_classes.append(class_info)
        
        # 模式2：查找var className = function(parentClass) { ... } 模式
        # 用于没有装饰器的简单类
        pattern2 = r'var\s+(\w+)\s*=\s*function\s*\((\w+)\)\s*\{[^}]*?function\s+(\w+)[^}]*?n\(\3,\s*\2\)[^}]*?\}\(([^)]+)\)'
        
        matches2 = re.finditer(pattern2, code, re.DOTALL)
        for match in matches2:
            class_var = match.group(1)
            parent_param = match.group(2)
            class_name = match.group(3)
            parent_class = match.group(4)
            
            class_info = {
                'start': match.start(),
                'end': match.end(),
                'full_match': match.group(0),
                'type': 'typescript_class',
                'class_var': class_var,
                'class_name': class_name,
                'decorators': '',
                'parent_class': parent_class,
                'parent_param': parent_param,
                'body': match.group(0)
            }
            
            ts_classes.append(class_info)
        
        return ts_classes
    
    def parse_cc_class_body(self, class_body):
        """解析cc.Class体，提取属性、方法等信息"""
        class_info = {
            'name': '',
            'extends': 'cc.Component',
            'properties': {},
            'methods': {},
            'statics': {},
            'mixins': []
        }
        
        # 提取类名
        name_patterns = [
            r'name\s*:\s*["\']([^"\']+)["\']',
            r'name\s*:\s*([^\s,\}]+)'
        ]
        
        for pattern in name_patterns:
            name_match = re.search(pattern, class_body)
            if name_match:
                class_info['name'] = name_match.group(1).strip()
                break
        
        #提取 继承关系
        extends_patterns = [
            r'extends\s*:\s*["\']([^"\']+)["\']',
            r'extends\s*:\s*([^\s,\}]+)'
        ]
        
        for pattern in extends_patterns:
            extends_match = re.search(pattern, class_body)
            if extends_match:
                class_info['extends'] = extends_match.group(1).strip()
                break
        
        # 提取属性（改进版本）
        # 首先查找properties字段
        properties_match = self._find_balanced_brace_content(class_body, 'properties')
        if properties_match:
            properties_str = properties_match
            # 解析属性对象
            self._parse_properties_object(properties_str, class_info)
        
        # 提取静态属性
        statics_match = self._find_balanced_brace_content(class_body, 'statics')
        if statics_match:
            statics_str = statics_match
            # 解析静态属性对象
            self._parse_statics_object(statics_str, class_info)
        
        # 提取方法（改进版本）
        # 首先查找methods字段
        methods_match = self._find_balanced_brace_content(class_body, 'methods')
        if methods_match:
            methods_str = methods_match
            # 解析方法对象
            self._parse_methods_object(methods_str, class_info)
        else:
            # 回退到正则表达式查找方法
            self._extract_methods_fallback(class_body, class_info)
        
        return class_info
    
    def _find_balanced_brace_content(self, text, key):
        """查找键对应的平衡花括号内容"""
        # 查找 key: { 的模式（支持各种空格格式）
        # 注意：使用 {{ 来表示字面量的 { 字符，避免 format 解析错误
        pattern = re.compile(r'{}\s*:\s*{{'.format(re.escape(key)), re.DOTALL)
        match = pattern.search(text)
        if not match:
            return None
        
        start_pos = match.end() - 1  # 指向 { 的位置
        brace_count = 0
        in_string = False
        string_char = None
        escape_next = False
        
        # 遍历文本找到匹配的 }
        for i in range(start_pos, len(text)):
            char = text[i]
            
            # 处理转义字符
            if escape_next:
                escape_next = False
                continue
            
            # 处理字符串
            if in_string:
                if char == '\\':
                    escape_next = True
                elif char == string_char:
                    in_string = False
                    string_char = None
                continue
            
            # 检查字符串开始
            if char in ('"', "'"):
                in_string = True
                string_char = char
                continue
            
            # 计算花括号
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    # 找到匹配的结束花括号
                    return text[start_pos + 1:i]  # 返回花括号内的内容
        
        return None
    
    def _parse_properties_object(self, properties_str, class_info):
        """解析属性对象"""
        # 使用改进的解析器处理对象内容
        props = self._parse_js_object(properties_str)
        for prop_name, prop_value in props.items():
            class_info['properties'][prop_name] = prop_value
    
    def _parse_statics_object(self, statics_str, class_info):
        """解析静态属性对象"""
        # 使用改进的解析器处理对象内容
        statics = self._parse_js_object(statics_str)
        for static_name, static_value in statics.items():
            class_info['statics'][static_name] = static_value
    
    def _parse_methods_object(self, methods_str, class_info):
        """解析方法对象"""
        # 使用改进的解析器处理对象内容
        methods = self._parse_js_object(methods_str)
        for method_name, method_value in methods.items():
            # 方法值可能是函数字符串
            class_info['methods'][method_name] = {
                'params': [],
                'body': method_value
            }
    
    def _parse_js_object(self, js_str):
        """解析JavaScript对象字符串为键值对"""
        result = {}
        pos = 0
        length = len(js_str)
        
        while pos < length:
            # 跳过空白字符
            while pos < length and js_str[pos].isspace():
                pos += 1
            
            if pos >= length:
                break
            
            # 查找键
            key = None
            if js_str[pos] in ('"', "'"):
                # 字符串键
                end_quote = js_str[pos]
                start = pos + 1
                pos = start
                while pos < length:
                    if js_str[pos] == '\\':
                        pos += 2  # 跳过转义字符
                        continue
                    if js_str[pos] == end_quote:
                        key = js_str[start:pos]
                        pos += 1
                        break
                    pos += 1
            else:
                # 标识符键
                start = pos
                while pos < length and (js_str[pos].isalnum() or js_str[pos] in ('_', '$')):
                    pos += 1
                if pos > start:
                    key = js_str[start:pos]
            
            if not key:
                pos += 1
                continue
            
            # 跳过空白字符和冒号
            while pos < length and (js_str[pos].isspace() or js_str[pos] == ':'):
                pos += 1
            
            if pos >= length:
                break
            
            # 查找值
            value_start = pos
            value = self._extract_js_value(js_str, pos)
            if value is not None:
                result[key] = value
                pos = value_start + len(value)
            else:
                # 无法解析值，跳过
                pos += 1
        
        return result
    
    def _extract_js_value(self, js_str, start_pos):
        """从指定位置提取JavaScript值"""
        pos = start_pos
        length = len(js_str)
        
        if pos >= length:
            return None
        
        char = js_str[pos]
        
        # 字符串
        if char in ('"', "'"):
            end_quote = char
            start = pos + 1
            pos = start
            while pos < length:
                if js_str[pos] == '\\':
                    pos += 2  # 跳过转义字符
                    continue
                if js_str[pos] == end_quote:
                    return js_str[start_pos:pos + 1]
                pos += 1
            return js_str[start_pos:]
        
        # 数字（简化处理）
        if char.isdigit() or char == '-':
            start = pos
            while pos < length and (js_str[pos].isdigit() or js_str[pos] in ('.', 'e', 'E', '+', '-')):
                pos += 1
            return js_str[start:pos]
        
        # 布尔值或null
        if js_str.startswith('true', pos):
            return 'true'
        elif js_str.startswith('false', pos):
            return 'false'
        elif js_str.startswith('null', pos):
            return 'null'
        
        # 数组
        if char == '[':
            return self._extract_balanced(js_str, pos, '[', ']')
        
        # 对象
        if char == '{':
            return self._extract_balanced(js_str, pos, '{', '}')
        
        # 函数
        if js_str.startswith('function', pos):
            # 查找函数结束
            func_end = self._find_function_end(js_str, pos)
            if func_end > pos:
                return js_str[pos:func_end]
        
        # 箭头函数
        if js_str.startswith('(', pos) or js_str.startswith('=>', pos):
            # 简化处理：提取到下一个逗号或结束符
            end = pos
            brace_count = 0
            paren_count = 0
            in_string = False
            string_char = None
            escape_next = False
            
            while end < length:
                c = js_str[end]
                
                if escape_next:
                    escape_next = False
                    end += 1
                    continue
                
                if in_string:
                    if c == '\\':
                        escape_next = True
                    elif c == string_char:
                        in_string = False
                        string_char = None
                    end += 1
                    continue
                
                if c in ('"', "'"):
                    in_string = True
                    string_char = c
                    end += 1
                    continue
                
                if c == '(':
                    paren_count += 1
                elif c == ')':
                    paren_count -= 1
                elif c == '{':
                    brace_count += 1
                elif c == '}':
                    brace_count -= 1
                elif c == ',' and paren_count == 0 and brace_count == 0:
                    break
                
                end += 1
            
            return js_str[pos:end]
        
        # 标识符（如cc.Label）
        start = pos
        while pos < length and (js_str[pos].isalnum() or js_str[pos] in ('.', '_', '$')):
            pos += 1
        if pos > start:
            return js_str[start:pos]
        
        return None
    
    def _extract_balanced(self, js_str, start_pos, open_char, close_char):
        """提取平衡的括号内容"""
        count = 0
        pos = start_pos
        length = len(js_str)
        in_string = False
        string_char = None
        escape_next = False
        
        while pos < length:
            char = js_str[pos]
            
            if escape_next:
                escape_next = False
                pos += 1
                continue
            
            if in_string:
                if char == '\\':
                    escape_next = True
                elif char == string_char:
                    in_string = False
                    string_char = None
                pos += 1
                continue
            
            if char in ('"', "'"):
                in_string = True
                string_char = char
                pos += 1
                continue
            
            if char == open_char:
                count += 1
            elif char == close_char:
                count -= 1
                if count == 0:
                    return js_str[start_pos:pos + 1]
            
            pos += 1
        
        return js_str[start_pos:]
    
    def _find_function_end(self, js_str, start_pos):
        """查找函数结束位置"""
        pos = start_pos
        length = len(js_str)
        brace_count = 0
        in_string = False
        string_char = None
        escape_next = False
        
        # 跳过function关键字
        pos += 8
        
        # 跳过参数
        while pos < length and js_str[pos] != '{':
            pos += 1
        
        if pos >= length or js_str[pos] != '{':
            return start_pos
        
        # 现在pos指向{
        brace_count = 1
        pos += 1
        
        while pos < length and brace_count > 0:
            char = js_str[pos]
            
            if escape_next:
                escape_next = False
                pos += 1
                continue
            
            if in_string:
                if char == '\\':
                    escape_next = True
                elif char == string_char:
                    in_string = False
                    string_char = None
                pos += 1
                continue
            
            if char in ('"', "'"):
                in_string = True
                string_char = char
                pos += 1
                continue
            
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            
            pos += 1
        
        return pos
    
    def _extract_methods_fallback(self, class_body, class_info):
        """回退方法提取（使用正则表达式）"""
        # 查找 xxx: function(...){...} 或 xxx(...){...}
        # 改进的正则表达式，避免匹配 Class: function({... 这样的模式
        method_patterns = [
            # 模式1: xxx: function(...) { ... } 
            # 使用非贪婪匹配，并确保参数列表不包含 { 或换行符
            r'(\w+)\s*:\s*function\s*\(([^){}\n]*)\)\s*\{([\s\S]*?)\}(?=\s*[,}])',
            # 模式2: xxx: (...) => { ... } (箭头函数)
            r'(\w+)\s*:\s*\(([^){}\n]*)\)\s*=>\s*\{([\s\S]*?)\}(?=\s*[,}])',
            # 模式3: xxx(...) { ... } (ES6简写方法)
            r'(\w+)\s*\(([^){}\n]*)\)\s*\{([\s\S]*?)\}(?=\s*[,}])'
        ]
        
        for pattern in method_patterns:
            try:
                method_matches = re.finditer(pattern, class_body, re.DOTALL)
                for match in method_matches:
                    method_name = match.group(1)
                    params = match.group(2)
                    method_body = match.group(3)
                    
                    # 跳过无效的方法名（如 Class, function 等）
                    if method_name.lower() in ['class', 'function', 'if', 'for', 'while', 'return']:
                        continue
                    
                    # 确保参数列表不包含 {（避免匹配 Class: function({ 的情况）
                    if '{' in params:
                        continue
                    
                    # 确保方法体不为空
                    if not method_body.strip():
                        continue
                    
                    class_info['methods'][method_name] = {
                        'params': [p.strip() for p in params.split(',') if p.strip()],
                        'body': method_body.strip()
                    }
            except Exception as e:
                # 如果正则表达式有错误，跳过这个模式
                continue
    
    def parse_typescript_class(self, class_def, decorator_mappings=None):
        """解析TypeScript装饰器类定义"""
        if decorator_mappings is None:
            decorator_mappings = {}
        class_info = {
            'name': '',
            'extends': 'cc.Component',
            'properties': {},
            'methods': {},
            'statics': {},
            'mixins': [],
            'decorators': []
        }
        
        # 从class_def中提取基本信息
        if class_def.get('class_name'):
            class_info['name'] = class_def['class_name']
        elif class_def.get('class_var'):
            class_info['name'] = class_def['class_var']
        
        if class_def.get('parent_class'):
            class_info['extends'] = class_def['parent_class']
        
        if class_def.get('decorators'):
            # 解析装饰器列表
            decorators = class_def['decorators'].split(',')
            for decorator in decorators:
                decorator = decorator.strip()
                if decorator:
                    # 将装饰器变量名映射为实际装饰器名
                    if decorator in decorator_mappings:
                        actual_decorator = decorator_mappings[decorator]
                        class_info['decorators'].append(actual_decorator)
                    else:
                        class_info['decorators'].append(decorator)
        
        # 从类体中提取方法和属性
        class_body = class_def.get('body', '')
        if class_body:
            # 提取方法：t.prototype.methodName = function(...) { ... }
            method_patterns = [
                r'(\w+)\.prototype\.(\w+)\s*=\s*function\s*\(([^)]*)\)\s*\{([\s\S]*?)\}(?=\s*[,;])',
                r'(\w+)\.prototype\.(\w+)\s*=\s*\(([^)]*)\)\s*=>\s*\{([\s\S]*?)\}(?=\s*[,;])',
                r'(\w+)\.prototype\.(\w+)\s*\(([^)]*)\)\s*\{([\s\S]*?)\}(?=\s*[,;])',
            ]
            
            for pattern in method_patterns:
                matches = re.finditer(pattern, class_body)
                for match in matches:
                    instance_var = match.group(1)  # 通常是 't'
                    method_name = match.group(2)
                    params = match.group(3)
                    method_body = match.group(4)
                    
                    class_info['methods'][method_name] = {
                        'params': [p.strip() for p in params.split(',') if p.strip()],
                        'body': method_body.strip()
                    }
            
            # 查找属性定义（可能通过装饰器定义）
            # 模式: Object.defineProperty(t.prototype, "propertyName", { ... })
            property_pattern = r'Object\.defineProperty\((\w+)\.prototype,\s*"([^"]+)"[^)]+\)'
            property_matches = re.finditer(property_pattern, class_body)
            for match in property_matches:
                instance_var = match.group(1)
                property_name = match.group(2)
                # 简单标记为属性
                class_info['properties'][property_name] = 'any'
        
        return class_info
    
    def convert_to_typescript(self, class_info):
        """将cc.Class信息转换为TypeScript格式"""
        ts_code = ""
        
        # 添加装饰器（如果有）
        decorators = class_info.get('decorators', [])
        for decorator in decorators:
            # 简化装饰器处理
            if 'ccclass' in decorator.lower():
                ts_code += f"@ccclass\n"
            elif 'property' in decorator.lower():
                # 尝试提取属性信息
                ts_code += f"@property\n"
            else:
                ts_code += f"@{decorator}\n"
        
        # 添加类定义
        if class_info.get('name'):
            ts_code += f"export class {class_info['name']} extends {class_info.get('extends', 'cc.Component')} {{\n"
        else:
            ts_code += f"export class UnknownClass extends {class_info.get('extends', 'cc.Component')} {{\n"
        
        # 添加属性
        for prop_name, prop_value in class_info.get('properties', {}).items():
            # 尝试推断类型
            prop_type = self._infer_type_from_value(prop_value)
            ts_code += f"    {prop_name}: {prop_type};\n"
        
        if class_info.get('properties'):
            ts_code += "\n"
        
        # 添加方法
        for method_name, method_info in class_info.get('methods', {}).items():
            params = method_info.get('params', [])
            param_str = ", ".join([f"{p}: any" for p in params])
            ts_code += f"    {method_name}({param_str}) {{\n"
            
            # 添加方法体占位符
            method_body = method_info.get('body', '')
            if method_body:
                # 保留原始方法体（可能需要进一步处理）
                body_lines = method_body.split('\n')
                for line in body_lines[:5]:  # 只保留前几行
                    ts_code += f"        {line}\n"
                if len(body_lines) > 5:
                    ts_code += f"        // ... 更多代码 ({len(body_lines)-5} 行)\n"
            else:
                ts_code += f"        // 方法实现\n"
            
            ts_code += f"    }}\n\n"
        
        ts_code += "}\n"
        return ts_code
    
    def convert_to_javascript(self, class_info):
        """将cc.Class信息转换为美化的JavaScript格式（类似参考工程）"""
        js_code = ""
        
        # 开始cc.Class定义
        js_code += "cc.Class({\n"
        
        # 添加类名（如果有）
        if class_info.get('name'):
            js_code += f"  name: '{class_info['name']}',\n"
        
        # 添加继承关系
        extends = class_info.get('extends', 'cc.Component')
        js_code += f"  extends: {extends},\n"
        
        # 添加属性
        properties = class_info.get('properties', {})
        if properties:
            js_code += "  properties: {\n"
            for prop_name, prop_value in properties.items():
                # 美化属性值：如果是对象或数组，保持原；样否则直接使用
                prop_value_str = str(prop_value).strip()
                js_code += f"    {prop_name}: {prop_value_str},\n"
            js_code = js_code.rstrip(",\n") + "\n  },\n"
        
        # 添加静态属性（如果有）
        statics = class_info.get('statics', {})
        if statics:
            js_code += "  statics: {\n"
            for static_name, static_value in statics.items():
                static_value_str = str(static_value).strip()
                js_code += f"    {static_name}: {static_value_str},\n"
            js_code = js_code.rstrip(",\n") + "\n  },\n"
        
        # 添加方法
        methods = class_info.get('methods', {})
        if methods:
            for method_name, method_info in methods.items():
                params = method_info.get('params', [])
                method_body = method_info.get('body', '')
                
                if method_body:
                    # 有方法体，尝试美化
                    # 将方法体缩进4个空格（相对于方法定义）
                    body_lines = method_body.split('\n')
                    indented_body = ""
                    for line in body_lines:
                        if line.strip():
                            indented_body += f"    {line}\n"  # 4空格缩进
                        else:
                            indented_body += "\n"
                    
                    # 移除末尾的换行
                    if indented_body.endswith("\n"):
                        indented_body = indented_body[:-1]
                    
                    if params:
                        param_str = ", ".join(params)
                        js_code += f"  {method_name}: function ({param_str}) {{\n"
                    else:
                        js_code += f"  {method_name}: function () {{\n"
                    
                    js_code += indented_body
                    js_code += f"\n  }},\n"  # 换行后加 },
                else:
                    # 只有方法占位符
                    if params:
                        param_str = ", ".join([f"{p}" for p in params])
                        js_code += f"  {method_name}: function ({param_str}) {{\n"
                    else:
                        js_code += f"  {method_name}: function () {{\n"
                    js_code += f"    // {method_name} 方法实现\n"
                    js_code += f"\n  }},\n"  # 换行后加 },
        
        # 添加默认的生命周期方法（如果没有定义）
        lifecycle_methods = ["onLoad", "start", "update", "lateUpdate", "onEnable", "onDisable", "onDestroy"]
        for lifecycle_method in lifecycle_methods:
            if lifecycle_method not in methods:
                if lifecycle_method == "update":
                    js_code += f"  {lifecycle_method}: function (dt) {{\n"
                else:
                    js_code += f"  {lifecycle_method}: function () {{\n"
                js_code += f"    // {lifecycle_method} 生命周期方法\n"
                js_code += f"  }},\n"
        
        # 移除最后一个逗号
        if js_code.endswith(",\n"):
            js_code = js_code[:-2] + "\n"
        
        js_code += "});"
        return js_code
    
    def _infer_type_from_value(self, value):
        """根据属性值推断TypeScript类型"""
        value_str = str(value).strip()
        
        if value_str.startswith('{') and value_str.endswith('}'):
            # 对象类型
            return 'any'  # 简化处理
        elif value_str.startswith('[') and value_str.endswith(']'):
            # 数组类型
            return 'any[]'
        elif value_str in ('true', 'false'):
            # 布尔类型
            return 'boolean'
        elif value_str.isdigit() or (value_str.startswith('-') and value_str[1:].isdigit()):
            # 数字类型
            return 'number'
        elif value_str.startswith('"') or value_str.startswith("'"):
            # 字符串类型
            return 'string'
        elif 'cc.' in value_str:
            # Cocos类型
            return value_str
        else:
            return 'any'
    
    def analyze_with_esprima(self, code):
        """使用esprima分析JavaScript代码"""
        if not ESPRIMA_AVAILABLE:
            return None
        
        try:
            ast = esprima.parseScript(code, {
                "range": True,
                "loc": True,
                "tolerant": True
            })
            return ast
        except Exception as e:
            print(f"esprima解析失败: {e}")
            return None
    
    def process_module_file(self, file_path, output_format='javascript', use_structured_ast=True):
        """处理单个模块文件
        Args:
            file_path: 模块文件路径
            output_format: 输出格式，'javascript' 或 'typescript'
            use_structured_ast: 是否使用结构化AST解析（产生更可读的代码）
        """
        print(f"处理模块文件: {file_path}")
        
        # 优先使用结构化AST解析（如果可用且启用）
        if use_structured_ast and ESPRIMA_AVAILABLE:
            try:
                result = self.process_module_with_structured_ast(file_path, output_format)
                if result:
                    print(f"  -> 使用结构化AST解析成功")
                    return result
                else:
                    print(f"  -> 结构化AST解析返回空，回退到传统解析")
            except Exception as e:
                print(f"  -> 结构化AST解析失败，回退到传统解析: {e}")
        
        # 传统解析方式
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"读取文件失败: {e}")
            return None
        
        # 提取内部代码
        inner_code = self.extract_inner_code(content)
        
        # 提取类名
        class_name = self.extract_class_name(content) or self.extract_class_name(inner_code)
        
        # 提取导出映射关系
        export_mappings = self.extract_export_mapping(content)
        
        # 提取装饰器映射关系
        decorator_mappings = self.extract_decorator_mapping(content)
        
        # 查找cc.Class定义
        class_definitions = self.find_cc_class_definitions(inner_code)
        
        if not class_definitions:
            print(f"  -> 未找到cc.Class定义，尝试美化整个JavaScript文件")
            
            results = []
            
            # 美化整个JavaScript文件
            beautified_code = self.beautify_javascript(content)
            
            # 创建伪类信息用于保存文件
            class_info = {
                'name': os.path.splitext(os.path.basename(file_path))[0],
                'extends': 'cc.Component',  # 默认值
                'properties': {},
                'methods': {},
                'is_general_js': True  # 标记为普通JavaScript文件
            }
            
            # 根据输出格式创建代码
            if output_format == 'javascript':
                # 对于普通JS文件，直接使用美化后的代码
                js_code = beautified_code
                # 添加文件头注释
                if not js_code.startswith('//'):
                    js_code = f"// 文件: {os.path.basename(file_path)}\n// 原始文件未包含cc.Class定义，已进行基本美化\n\n{js_code}"
            else:
                # TypeScript模式：尝试转换为TypeScript（但这里保持JavaScript格式）
                js_code = beautified_code
            
            results.append({
                'file_path': file_path,
                'class_info': class_info,
                'output_format': output_format,
                'js_code': js_code if output_format == 'javascript' else None,
                'ts_code': js_code if output_format == 'typescript' else None,
                'original_body': content[:200] + "..." if len(content) > 200 else content,
                'is_general_js': True  # 标记为普通JavaScript文件
            })
            
            return results
        
        print(f"  -> 找到 {len(class_definitions)} 个cc.Class定义")
        
        results = []
        for i, class_def in enumerate(class_definitions):
            if class_def.get('type') == 'cc_class':
                class_info = self.parse_cc_class_body(class_def['body'])
            elif class_def.get('type') == 'typescript_class':
                class_info = self.parse_typescript_class(class_def, decorator_mappings)
            else:
                # 默认使用cc_class解析
                class_info = self.parse_cc_class_body(class_def['body'])
            
            # 确定类名（优先级从高到低）:
            # 1. 从导出映射中获取（如果类变量名在映射中）
            # 2. 从extract_class_name提取的类名
            # 3. 从class_def中提取的类名
            # 4. 从class_def中提取的类变量名
            # 5. 默认UnknownClass
            
            final_class_name = None
            
            # 首先检查导出映射
            class_var_name = class_def.get('class_var')
            if class_var_name and class_var_name in export_mappings:
                final_class_name = export_mappings[class_var_name]
                print(f"  -> 通过导出映射找到类名: {class_var_name} -> {final_class_name}")
            elif class_name:
                final_class_name = class_name
            elif class_def.get('class_name'):
                final_class_name = class_def.get('class_name')
            elif class_def.get('class_var'):
                final_class_name = class_def.get('class_var')
            else:
                final_class_name = f"UnknownClass_{i+1}"
            
            class_info['name'] = final_class_name
            
            # 如果继承关系为空，尝试从class_def中获取
            if not class_info.get('extends') and class_def.get('parent_class'):
                class_info['extends'] = class_def.get('parent_class')
            
            print(f"  -> 类: {class_info['name']}, 继承自: {class_info.get('extends', 'cc.Component')}")
            print(f"     属性: {len(class_info.get('properties', {}))}, 方法: {len(class_info.get('methods', {}))}")
            
            # 根据输出格式转换代码
            if output_format == 'javascript':
                code = self.convert_to_javascript(class_info)
                code_key = 'js_code'
            else:  # typescript
                code = self.convert_to_typescript(class_info)
                code_key = 'ts_code'
            
            results.append({
                'file_path': file_path,
                'class_info': class_info,
                'output_format': output_format,
                'ts_code': code if output_format == 'typescript' else None,
                'js_code': code if output_format == 'javascript' else None,
                'original_body': class_def.get('body', class_def.get('full_match', ''))[:200] + "..." if len(class_def.get('body', class_def.get('full_match', ''))) > 200 else class_def.get('body', class_def.get('full_match', ''))
            })
        
        return results
    
    def save_typescript_file(self, class_info, ts_code, output_dir, original_filename=None):
        """保存TypeScript文件"""
        if not class_info['name']:
            class_name = "UnknownClass"
        else:
            class_name = class_info['name']
        
        # 清理类名，确保是安全的文件名
        safe_class_name = re.sub(r'[\\/*?:"<>|]', '_', class_name)
        
        if original_filename:
            # 保持原始文件名，但改为.ts扩展名
            base_name = os.path.splitext(original_filename)[0]
            ts_filename = f"{base_name}.ts"
        else:
            ts_filename = f"{safe_class_name}.ts"
        
        output_path = os.path.join(output_dir, ts_filename)
        
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(ts_code)
            print(f"  -> 保存TypeScript文件: {output_path}")
            return output_path
        except Exception as e:
            print(f"  -> 保存文件失败: {e}")
            return None
    
    def beautify_javascript(self, js_code):
        """改进的JavaScript代码美化（基于AST感知的格式调整）"""
        if not js_code:
            return js_code
        
        # 尝试使用esprima进行AST解析和美化
        if ESPRIMA_AVAILABLE:
            try:
                return self.beautify_javascript_with_ast(js_code)
            except Exception as e:
                print(f"AST美化失败，使用基础美化: {e}")
                # 回退到基础美化
        
        # 基础美化策略（字符级处理）
        result = []
        indent_level = 0
        in_string = False
        string_char = None  # 记录当前字符串引号类型 ' 或 "
        escaped = False  # 是否在转义字符中
        bracket_stack = []  # 跟踪括号类型: '(' '[' '{'
        
        i = 0
        while i < len(js_code):
            ch = js_code[i]
            
            # 处理转义字符
            if escaped:
                result.append(ch)
                escaped = False
                i += 1
                continue
            
            # 处理字符串
            if in_string:
                result.append(ch)
                if ch == '\\':
                    escaped = True
                elif ch == string_char:
                    in_string = False
                    string_char = None
                i += 1
                continue
            
            # 开始字符串
            if ch in ['"', "'", '`']:
                in_string = True
                string_char = ch
                result.append(ch)
                i += 1
                continue
            
            # 处理括号入栈
            if ch in '({[':
                bracket_stack.append(ch)
                result.append(ch)
                # 如果是花括号，换行并增加缩进
                if ch == '{':
                    result.append('\n')
                    indent_level += 1
                    result.append('  ' * indent_level)
                elif ch == '[':
                    # 方括号内不换行，除非内容很长
                    pass
                else:  # 圆括号
                    # 函数调用参数通常不换行
                    pass
            elif ch in ')}]':
                if bracket_stack:
                    opening = bracket_stack.pop()
                    # 确保括号匹配
                    if (opening == '(' and ch == ')') or (opening == '[' and ch == ']') or (opening == '{' and ch == '}'):
                        if opening == '{':
                            # 花括号闭合：减少缩进
                            indent_level = max(0, indent_level - 1)
                            result.append('\n')
                            result.append('  ' * indent_level)
                            result.append(ch)
                            # 闭合后换行（如果不是对象字面量）
                            if i + 1 < len(js_code) and js_code[i+1] not in ',;':
                                result.append('\n')
                                result.append('  ' * indent_level)
                        elif opening == '[':
                            # 方括号闭合
                            result.append(ch)
                        else:  # 圆括号闭合
                            result.append(ch)
                    else:
                        # 括号不匹配，保持原样
                        result.append(ch)
                else:
                    result.append(ch)
            elif ch == ';':
                result.append(ch)
                # 分号后换行（但避免在for循环中过度换行）
                # 检查是否是for循环的一部分
                is_in_for = False
                if i >= 2 and js_code[i-2:i+1] == 'for':
                    is_in_for = True
                
                if not is_in_for:
                    result.append('\n')
                    result.append('  ' * indent_level)
            elif ch == ',':
                result.append(ch)
                # 逗号后换行取决于上下文
                # 如果在对象或数组中，考虑换行
                if bracket_stack and bracket_stack[-1] in '{[':
                    # 对象或数组内的逗号，换行以获得更好的可读性
                    result.append('\n')
                    result.append('  ' * indent_level)
                else:
                    # 函数参数或其他上下文中的逗号，不换行
                    result.append(' ')
            else:
                result.append(ch)
            
            i += 1
        
        beautified = ''.join(result)
        
        # 后处理：清理多余的空格和空行
        lines = beautified.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped:
                # 移除行尾多余空格
                cleaned_lines.append(line.rstrip())
            elif cleaned_lines and cleaned_lines[-1].strip():
                # 只保留一个空行
                cleaned_lines.append('')
        
        return '\n'.join(cleaned_lines)
    
    def beautify_javascript_with_ast(self, js_code):
        """使用AST进行JavaScript代码美化"""
        try:
            ast = esprima.parseScript(js_code, {
                "range": True,
                "loc": True,
                "tolerant": True
            })
            
            # 使用AST生成格式良好的代码
            # 这里实现一个简单的AST到代码的转换器
            # 参考用户提供的代码结构
            return self._generate_code_from_ast(ast)
        except Exception as e:
            raise Exception(f"AST解析失败: {e}")
    
    def _generate_code_from_ast(self, ast_node):
        """从AST节点生成格式良好的JavaScript代码"""
        # 这是一个简化的AST到代码转换器
        # 实际实现需要处理所有AST节点类型
        # 这里提供一个基础框架
        
        node_type = ast_node.get("type") if isinstance(ast_node, dict) else None
        
        if not node_type:
            return str(ast_node)
        
        if node_type == "Program":
            # 程序根节点
            body = ast_node.get("body", [])
            statements = []
            for stmt in body:
                code = self._generate_code_from_ast(stmt)
                if code:
                    statements.append(code)
            return "\n".join(statements)
        
        elif node_type == "ExpressionStatement":
            # 表达式语句
            expression = ast_node.get("expression")
            if expression:
                code = self._generate_code_from_ast(expression)
                return f"{code};" if not code.endswith(";") else code
        
        elif node_type == "CallExpression":
            # 函数调用
            callee = self._generate_code_from_ast(ast_node.get("callee", {}))
            arguments = ast_node.get("arguments", [])
            args_list = []
            for arg in arguments:
                args_list.append(self._generate_code_from_ast(arg))
            args_str = ", ".join(args_list)
            return f"{callee}({args_str})"
        
        elif node_type == "MemberExpression":
            # 成员表达式 obj.property
            object_code = self._generate_code_from_ast(ast_node.get("object", {}))
            property_code = self._generate_code_from_ast(ast_node.get("property", {}))
            if ast_node.get("computed", False):
                return f"{object_code}[{property_code}]"
            else:
                return f"{object_code}.{property_code}"
        
        elif node_type == "Identifier":
            # 标识符
            return ast_node.get("name", "")
        
        elif node_type == "Literal":
            # 字面量
            value = ast_node.get("value")
            if isinstance(value, str):
                # 简单字符串处理
                return f"'{value}'"
            else:
                return str(value)
        
        elif node_type == "ObjectExpression":
            # 对象表达式 { key: value, ... }
            properties = ast_node.get("properties", [])
            if not properties:
                return "{}"
            
            prop_list = []
            for prop in properties:
                key = self._generate_code_from_ast(prop.get("key", {}))
                value = self._generate_code_from_ast(prop.get("value", {}))
                prop_list.append(f"  {key}: {value}")
            
            return "{\n" + ",\n".join(prop_list) + "\n}"
        
        elif node_type == "FunctionExpression":
            # 函数表达式
            params = ast_node.get("params", [])
            body = ast_node.get("body", {})
            
            params_list = []
            for param in params:
                params_list.append(self._generate_code_from_ast(param))
            params_str = ", ".join(params_list)
            
            body_code = self._generate_code_from_ast(body)
            
            return f"function({params_str}) {body_code}"
        
        elif node_type == "BlockStatement":
            # 代码块 { ... }
            body = ast_node.get("body", [])
            if not body:
                return "{}"
            
            statements = []
            for stmt in body:
                stmt_code = self._generate_code_from_ast(stmt)
                if stmt_code:
                    statements.append(f"  {stmt_code}")
            
            return "{\n" + "\n".join(statements) + "\n}"
        
        # 更多节点类型处理...
        else:
            # 对于未处理的节点类型，返回原始文本（如果可能）
            if "range" in ast_node:
                start, end = ast_node["range"]
                return js_code[start:end]
            else:
                return f"/* {node_type} */"
    
    def save_javascript_file(self, class_info, js_code, output_dir, original_filename=None):
        """保存JavaScript文件（美化格式，类似参考工程）"""
        if not class_info['name']:
            class_name = "UnknownClass"
        else:
            class_name = class_info['name']
        
        # 清理类名，确保是安全的文件名
        safe_class_name = re.sub(r'[\\/*?:"<>|]', '_', class_name)
        
        if original_filename:
            # 保持原始文件名，但使用.js扩展名
            base_name = os.path.splitext(original_filename)[0]
            js_filename = f"{base_name}.js"
        else:
            js_filename = f"{safe_class_name}.js"
        
        output_path = os.path.join(output_dir, js_filename)
        
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(js_code)
            print(f"  -> 保存JavaScript文件: {output_path}")
            return output_path
        except Exception as e:
            print(f"  -> 保存JavaScript文件失败: {e}")
            return None
    
    # ------------------------------------------------------------
    # 基于AST的结构化代码解析和生成（按照用户参考代码模式）
    # ------------------------------------------------------------
    
    def walk(self, node, visitor):
        """AST遍历辅助函数（参考用户代码）"""
        if isinstance(node, dict):
            visitor(node)
            for v in node.values():
                self.walk(v, visitor)
        elif isinstance(node, list):
            for i in node:
                self.walk(i, visitor)
    
    def parse_module_with_ast(self, js_code):
        """使用AST解析JavaScript模块（参考用户代码模式）
        
        Args:
            js_code: JavaScript代码字符串
        
        Returns:
            dict: 解析结果，包含模块名、依赖、静态字段等信息
        """
        if not ESPRIMA_AVAILABLE:
            print("警告: esprima不可用，无法进行AST解析")
            return None
        
        try:
            # 解析为AST
            ast = esprima.parseScript(js_code, {
                "range": True,
                "loc": True,
                "tolerant": True
            })
            
            # 解析上下文
            ctx = {
                "module_name": None,
                "class_name": None,
                "imports": {},      # name -> path
                "static_fields": {}, # field -> type
                "static_props": {},  # prop -> type (getter/setter)
                "classes": [],       # 类定义列表
                "functions": [],     # 函数定义列表
                "variables": {},     # 变量定义
            }
            
            # 1. 查找模块名（cc._RF.push）
            def find_module_name(node):
                if node.get("type") == "CallExpression":
                    callee = node.get("callee", {})
                    if callee.get("property", {}).get("name") == "push":
                        args = node.get("arguments", [])
                        if len(args) >= 3 and args[2]["type"] == "Literal":
                            ctx["module_name"] = args[2]["value"]
                            ctx["class_name"] = ctx["module_name"]
            
            # 2. 查找导入依赖（require/e调用）
            def find_imports(node):
                if node.get("type") == "CallExpression":
                    callee = node.get("callee", {})
                    # 处理 require() 或 e() 调用
                    if callee.get("name") in ["e", "require"]:
                        args = node.get("arguments", [])
                        if args and args[0]["type"] == "Literal":
                            path = args[0]["value"]
                            # 从路径中提取名称
                            name = os.path.basename(path)
                            if "." in name:
                                name = name.split(".")[0]
                            ctx["imports"][name] = path
            
            # 3. 查找静态字段（e._xxx = value）
            def find_static_fields(node):
                if node.get("type") == "AssignmentExpression":
                    left = node["left"]
                    if (left.get("type") == "MemberExpression" and 
                        left.get("object", {}).get("name") == "e"):
                        field = left["property"]["name"]
                        right = node["right"]
                        # 推断类型
                        ts_type = "any"
                        if right["type"] == "Literal":
                            value = right["value"]
                            if isinstance(value, bool):
                                ts_type = "boolean"
                            elif isinstance(value, (int, float)):
                                ts_type = "number"
                            elif isinstance(value, str):
                                ts_type = "string"
                            elif value is None:
                                ts_type = "any"
                        ctx["static_fields"][field] = ts_type
            
            # 4. 查找Object.defineProperty定义
            def find_define_property(node):
                if node.get("type") == "CallExpression":
                    callee = node.get("callee", {})
                    if callee.get("property", {}).get("name") == "defineProperty":
                        args = node.get("arguments", [])
                        if len(args) >= 3:
                            prop_name = args[1]["value"]
                            descriptor = args[2]
                            if descriptor["type"] == "ObjectExpression":
                                # 查找getter/setter
                                for prop in descriptor.get("properties", []):
                                    if prop["key"]["name"] in ["get", "set"]:
                                        ctx["static_props"][prop_name] = "any"
                                        break
            
            # 5. 查找类定义（包括cc.Class和普通类）
            def find_class_definitions(node):
                # cc.Class定义
                if node.get("type") == "CallExpression":
                    callee = node.get("callee", {})
                    if (callee.get("type") == "MemberExpression" and 
                        callee.get("object", {}).get("name") == "cc" and 
                        callee.get("property", {}).get("name") == "Class"):
                        # 找到cc.Class定义
                        class_info = self._extract_cc_class_info(node)
                        if class_info:
                            ctx["classes"].append(class_info)
                
                # ES6类定义
                elif node.get("type") == "ClassDeclaration":
                    class_info = self._extract_es6_class_info(node)
                    if class_info:
                        ctx["classes"].append(class_info)
            
            # 遍历AST应用所有查找器
            def visit_all(node):
                find_module_name(node)
                find_imports(node)
                find_static_fields(node)
                find_define_property(node)
                find_class_definitions(node)
            
            self.walk(ast, visit_all)
            
            # 如果没找到模块名，尝试从文件名或其他信息推断
            if not ctx["module_name"]:
                # 可以尝试从其他上下文推断
                pass
            
            return ctx
            
        except Exception as e:
            print(f"AST解析失败: {e}")
            return None
    
    def _extract_cc_class_info(self, call_node):
        """提取cc.Class的信息"""
        args = call_node.get("arguments", [])
        if not args:
            return None
        
        class_obj = args[0]
        if class_obj["type"] != "ObjectExpression":
            return None
        
        class_info = {
            "type": "cc_class",
            "name": None,
            "extends": "cc.Component",
            "properties": {},
            "methods": {},
            "statics": {},
        }
        
        # 提取类属性
        for prop in class_obj.get("properties", []):
            key = prop.get("key", {})
            value = prop.get("value", {})
            
            if key.get("type") == "Identifier":
                prop_name = key.get("name")
                
                # 类名
                if prop_name == "name" and value.get("type") == "Literal":
                    class_info["name"] = value.get("value")
                
                # 继承关系
                elif prop_name == "extends":
                    if value.get("type") == "Identifier":
                        class_info["extends"] = value.get("name")
                    elif value.get("type") == "MemberExpression":
                        # 提取完整路径如 cc.Component
                        extends_path = []
                        curr = value
                        while curr and curr.get("type") == "MemberExpression":
                            if curr.get("property", {}).get("name"):
                                extends_path.insert(0, curr.get("property").get("name"))
                            curr = curr.get("object")
                        if curr and curr.get("type") == "Identifier":
                            extends_path.insert(0, curr.get("name"))
                        class_info["extends"] = ".".join(extends_path)
                
                # 属性定义
                elif prop_name == "properties" and value.get("type") == "ObjectExpression":
                    for prop_def in value.get("properties", []):
                        prop_def_key = prop_def.get("key", {})
                        prop_def_value = prop_def.get("value", {})
                        if prop_def_key.get("type") == "Identifier":
                            prop_name = prop_def_key.get("name")
                            class_info["properties"][prop_name] = self._extract_property_value(prop_def_value)
                
                # 静态属性
                elif prop_name == "statics" and value.get("type") == "ObjectExpression":
                    for static_def in value.get("properties", []):
                        static_def_key = static_def.get("key", {})
                        static_def_value = static_def.get("value", {})
                        if static_def_key.get("type") == "Identifier":
                            static_name = static_def_key.get("name")
                            class_info["statics"][static_name] = self._extract_property_value(static_def_value)
                
                # 方法定义
                elif value.get("type") in ["FunctionExpression", "ArrowFunctionExpression"]:
                    method_info = {
                        "params": [],
                        "body": self._extract_method_body(value),
                        "is_arrow": value.get("type") == "ArrowFunctionExpression"
                    }
                    # 提取参数
                    if value.get("params"):
                        for param in value.get("params"):
                            if param.get("type") == "Identifier":
                                method_info["params"].append(param.get("name"))
                    class_info["methods"][prop_name] = method_info
        
        return class_info
    
    def _extract_es6_class_info(self, class_node):
        """提取ES6类定义信息"""
        class_info = {
            "type": "es6_class",
            "name": class_node.get("id", {}).get("name"),
            "extends": None,
            "methods": {},
            "properties": {},
        }
        
        # 提取继承关系
        if class_node.get("superClass"):
            super_class = class_node["superClass"]
            if super_class.get("type") == "Identifier":
                class_info["extends"] = super_class.get("name")
        
        # 提取类体
        body = class_node.get("body", {})
        if body.get("type") == "ClassBody":
            for method in body.get("body", []):
                if method.get("type") == "MethodDefinition":
                    key = method.get("key", {})
                    value = method.get("value", {})
                    if key.get("type") == "Identifier":
                        method_name = key.get("name")
                        if value.get("type") == "FunctionExpression":
                            method_info = {
                                "params": [],
                                "body": self._extract_method_body(value),
                                "is_static": method.get("static", False)
                            }
                            # 提取参数
                            if value.get("params"):
                                for param in value.get("params"):
                                    if param.get("type") == "Identifier":
                                        method_info["params"].append(param.get("name"))
                            class_info["methods"][method_name] = method_info
        
        return class_info
    
    def _extract_property_value(self, value_node):
        """提取属性值"""
        value_type = value_node.get("type")
        
        if value_type == "Literal":
            return value_node.get("value")
        elif value_type == "ObjectExpression":
            obj = {}
            for prop in value_node.get("properties", []):
                prop_key = prop.get("key", {})
                prop_val = prop.get("value", {})
                if prop_key:
                    if prop_key.get("type") == "Identifier":
                        key_name = prop_key.get("name")
                    elif prop_key.get("type") == "Literal":
                        key_name = prop_key.get("value")
                    else:
                        continue
                    obj[key_name] = self._extract_property_value(prop_val)
            return obj
        elif value_type == "ArrayExpression":
            arr = []
            for elem in value_node.get("elements", []):
                if elem:
                    arr.append(self._extract_property_value(elem))
            return arr
        elif value_type == "MemberExpression":
            # 提取成员表达式路径
            path = []
            curr = value_node
            while curr:
                if curr.get("property", {}).get("name"):
                    path.insert(0, curr.get("property").get("name"))
                curr = curr.get("object")
                if curr and curr.get("type") == "Identifier":
                    path.insert(0, curr.get("name"))
                    break
            return ".".join(path)
        else:
            return f"<{value_type}>"
    
    def _extract_method_body(self, func_node):
        """提取方法体"""
        body_node = func_node.get("body")
        if not body_node or body_node.get("type") != "BlockStatement":
            return ""
        
        # 简化：返回占位符
        return "// 方法实现"
    
    def generate_structured_typescript(self, ctx, original_filename=None):
        """生成结构化的TypeScript代码（参考用户代码模式）
        
        Args:
            ctx: 解析上下文
            original_filename: 原始文件名（用于类名推断）
        
        Returns:
            str: 生成的TypeScript代码
        """
        lines = []
        
        # 1. 导入语句
        for name, path in ctx.get("imports", {}).items():
            # 简化路径处理
            lines.append(f'import {{ {name} }} from "{path}";')
        
        if ctx.get("imports"):
            lines.append("")
        
        # 2. 类定义（如果有多个类，生成多个类）
        classes = ctx.get("classes", [])
        if classes:
            for class_info in classes:
                class_name = class_info.get("name") or ctx.get("class_name") or "UnknownClass"
                extends = class_info.get("extends", "cc.Component")
                
                lines.append(f"export class {class_name} extends {extends} {{")
                
                # 静态字段
                for field, field_type in ctx.get("static_fields", {}).items():
                    lines.append(f"  private static {field}: {field_type};")
                
                # 静态属性（getter/setter）
                for prop, prop_type in ctx.get("static_props", {}).items():
                    backing = f"_{prop}"
                    lines.append("")
                    lines.append(f"  static get {prop}(): {prop_type} {{")
                    lines.append(f"    return this.{backing};")
                    lines.append("  }")
                    lines.append("")
                    lines.append(f"  static set {prop}(value: {prop_type}) {{")
                    lines.append(f"    this.{backing} = value;")
                    lines.append("  }")
                
                # 实例属性
                properties = class_info.get("properties", {})
                if properties:
                    lines.append("")
                    for prop_name, prop_value in properties.items():
                        prop_type = "any"
                        if isinstance(prop_value, dict):
                            # 尝试从属性定义中提取类型
                            if "type" in prop_value:
                                prop_type = prop_value["type"]
                            elif "default" in prop_value:
                                default_val = prop_value["default"]
                                if isinstance(default_val, bool):
                                    prop_type = "boolean"
                                elif isinstance(default_val, (int, float)):
                                    prop_type = "number"
                                elif isinstance(default_val, str):
                                    prop_type = "string"
                        lines.append(f"  {prop_name}: {prop_type};")
                
                # 方法
                methods = class_info.get("methods", {})
                if methods:
                    lines.append("")
                    for method_name, method_info in methods.items():
                        params = method_info.get("params", [])
                        param_str = ", ".join([f"{p}: any" for p in params])
                        lines.append(f"  {method_name}({param_str}) {{")
                        lines.append(f"    {method_info.get('body', '// 方法实现')}")
                        lines.append("  }")
                        lines.append("")
                
                lines.append("}")
                lines.append("")  # 类之间的空行
        else:
            # 没有明确的类定义，生成一个默认类
            class_name = ctx.get("class_name") or (original_filename and os.path.splitext(original_filename)[0]) or "GeneratedClass"
            lines.append(f"export class {class_name} {{")
            lines.append("  // 自动生成的类")
            lines.append("}")
            lines.append("")
        
        return "\n".join(lines)
    
    def generate_structured_javascript(self, ctx, original_filename=None):
        """生成结构化的JavaScript代码"""
        ts_code = self.generate_structured_typescript(ctx, original_filename)
        
        # 简化：将TypeScript转换为JavaScript（移除类型注解）
        js_code = ts_code
        
        # 移除类型注解的简单处理
        lines = js_code.split("\n")
        cleaned_lines = []
        for line in lines:
            # 简单的类型注解移除
            line = re.sub(r':\s*[a-zA-Z_][a-zA-Z0-9_<>\[\]]*\s*(?=[,);{])', '', line)
            # 移除 import 语句
            if line.strip().startswith("import "):
                continue
            # 保留 export
            if line.strip().startswith("export "):
                line = line.replace("export ", "")
            cleaned_lines.append(line)
        
        return "\n".join(cleaned_lines)
    
    def _fallback_basic_process(self, file_path, output_format='javascript'):
        """基础美化处理（避免递归调用）"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"读取文件失败: {e}")
            return None
        
        # 美化代码
        beautified_code = self.beautify_javascript(content)
        
        # 创建类信息
        class_info = {
            'name': os.path.splitext(os.path.basename(file_path))[0],
            'extends': 'cc.Component',
            'properties': {},
            'methods': {},
            'is_general_js': True
        }
        
        # 根据输出格式创建代码
        if output_format == 'javascript':
            js_code = beautified_code
            if not js_code.startswith('//'):
                js_code = f"// 文件: {os.path.basename(file_path)}\n// AST解析失败，使用基础美化\n\n{js_code}"
        else:
            js_code = beautified_code
        
        result = {
            'file_path': file_path,
            'class_info': class_info,
            'output_format': output_format,
            'js_code': js_code if output_format == 'javascript' else None,
            'ts_code': js_code if output_format == 'typescript' else None,
            'original_body': content[:200] + "..." if len(content) > 200 else content,
            'is_general_js': True
        }
        
        return [result]
    
    def process_module_with_structured_ast(self, file_path, output_format='javascript'):
        """使用结构化AST解析处理模块文件
        
        Args:
            file_path: 文件路径
            output_format: 'javascript' 或 'typescript'
        
        Returns:
            list: 处理结果列表
        """
        print(f"使用结构化AST处理模块文件: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"读取文件失败: {e}")
            return None
        
        # 使用AST解析
        ctx = self.parse_module_with_ast(content)
        
        if not ctx:
            print(f"  -> AST解析失败，回退到基础美化处理")
            return self._fallback_basic_process(file_path, output_format)
        
        # 生成代码
        if output_format == 'typescript':
            code = self.generate_structured_typescript(ctx, os.path.basename(file_path))
        else:
            code = self.generate_structured_javascript(ctx, os.path.basename(file_path))
        
        # 构建返回结果
        class_info = {
            "name": ctx.get("class_name") or os.path.splitext(os.path.basename(file_path))[0],
            "extends": "cc.Component",  # 默认值
            "properties": {},
            "methods": {},
            "is_structured_ast": True,
        }
        
        # 如果有类定义，使用第一个类的信息
        classes = ctx.get("classes", [])
        if classes and classes[0].get("name"):
            first_class = classes[0]
            class_info.update({
                "name": first_class.get("name"),
                "extends": first_class.get("extends", "cc.Component"),
                "properties": first_class.get("properties", {}),
                "methods": first_class.get("methods", {}),
            })
        
        result = {
            "file_path": file_path,
            "class_info": class_info,
            "output_format": output_format,
            "js_code": code if output_format == 'javascript' else None,
            "ts_code": code if output_format == 'typescript' else None,
            "ast_context": ctx,
            "is_structured_ast": True,
        }
        
        return [result]

def main():
    """主函数"""
    # 测试处理fhpoker中的模块
    script_dir = r"C:\Workflow\xsh5\build\web-mobile\assets\fhpoker\script"
    
    if not os.path.exists(script_dir):
        print(f"脚本目录不存在: {script_dir}")
        return
    
    converter = ModuleConverter()
    
    # 获取所有.js文件
    js_files = [f for f in os.listdir(script_dir) if f.endswith('.js')]
    print(f"找到 {len(js_files)} 个模块文件")
    
    # 创建输出目录
    output_dir = os.path.join(script_dir, "typescript")
    
    # 处理每个文件
    for i, js_file in enumerate(js_files[:5]):  # 先处理前5个文件
        file_path = os.path.join(script_dir, js_file)
        print(f"\n[{i+1}/{len(js_files[:5])}] 处理: {js_file}")
        
        results = converter.process_module_file(file_path)
        
        if results:
            for result in results:
                # 保存TypeScript文件
                converter.save_typescript_file(
                    result['class_info'], 
                    result['ts_code'], 
                    output_dir,
                    js_file
                )
        else:
            print(f"  -> 未提取到类信息")
    
    print(f"\n处理完成! TypeScript文件保存到: {output_dir}")

if __name__ == "__main__":
    main()