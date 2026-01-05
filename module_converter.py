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
        
        # 提取继承关系
        extends_patterns = [
            r'extends\s*:\s*["\']([^"\']+)["\']',
            r'extends\s*:\s*([^\s,\}]+)'
        ]
        
        for pattern in extends_patterns:
            extends_match = re.search(pattern, class_body)
            if extends_match:
                class_info['extends'] = extends_match.group(1).strip()
                break
        
        # 提取属性
        properties_pattern = r'properties\s*:\s*\{([\s\S]*?)\}(?=\s*[,}])'
        properties_match = re.search(properties_pattern, class_body)
        if properties_match:
            properties_str = properties_match.group(1)
            # 简单解析属性键值对
            prop_pattern = r'(\w+)\s*:\s*({[^}]+}|\[[^\]]+\]|[^,}]+)'
            prop_matches = re.findall(prop_pattern, properties_str)
            for prop_name, prop_value in prop_matches:
                class_info['properties'][prop_name.strip()] = prop_value.strip()
        
        # 提取方法（简化版本）
        # 查找 xxx: function(...){...} 或 xxx(...){...}
        method_patterns = [
            r'(\w+)\s*:\s*function\s*\(([^)]*)\)\s*\{([\s\S]*?)\}(?=\s*[,}])',
            r'(\w+)\s*:\s*\(([^)]*)\)\s*=>\s*\{([\s\S]*?)\}(?=\s*[,}])',
            r'(\w+)\s*\(([^)]*)\)\s*\{([\s\S]*?)\}(?=\s*[,}])'
        ]
        
        for pattern in method_patterns:
            method_matches = re.finditer(pattern, class_body)
            for match in method_matches:
                method_name = match.group(1)
                params = match.group(2)
                method_body = match.group(3)
                
                class_info['methods'][method_name] = {
                    'params': [p.strip() for p in params.split(',') if p.strip()],
                    'body': method_body.strip()
                }
        
        return class_info
    
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
    
    def process_module_file(self, file_path):
        """处理单个模块文件"""
        print(f"处理模块文件: {file_path}")
        
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
            print(f"  -> 未找到cc.Class定义")
            return None
        
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
            
            # 转换为TypeScript
            ts_code = self.convert_to_typescript(class_info)
            
            results.append({
                'file_path': file_path,
                'class_info': class_info,
                'ts_code': ts_code,
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