#!/usr/bin/env python3
"""
module_converter.py - JavaScript模块转换器
"""

import os
import re
import json


class ModuleConverter:
    """JavaScript模块转换器"""
    
    def __init__(self):
        self.converted_files = []
    
    def process_module_file(self, file_path, output_format='javascript'):
        """
        处理单个模块文件
        
        Args:
            file_path: 模块文件路径
            output_format: 输出格式，'javascript' 或 'typescript'
        
        Returns:
            list: 转换结果列表
        """
        results = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取cc.Class定义
            class_pattern = r'cc\.Class\s*\(\s*\{([\s\S]*?)\}\s*\)'
            matches = re.finditer(class_pattern, content)
            
            for i, match in enumerate(matches):
                class_body = match.group(1)
                class_info = self._extract_class_info(class_body, file_path)
                
                if output_format == 'typescript':
                    ts_code = self._generate_typescript_code(class_info)
                    results.append({
                        'class_info': class_info,
                        'ts_code': ts_code,
                        'js_code': None
                    })
                else:
                    js_code = self._generate_javascript_code(class_info)
                    results.append({
                        'class_info': class_info,
                        'js_code': js_code,
                        'ts_code': None
                    })
            
        except Exception as e:
            print(f"处理模块文件失败 {file_path}: {e}")
        
        return results
    
    def process_module_with_structured_ast(self, file_path, output_format='javascript'):
        """
        使用结构化AST处理模块文件
        
        Args:
            file_path: 模块文件路径
            output_format: 输出格式，'javascript' 或 'typescript'
        
        Returns:
            list: 转换结果列表
        """
        # 简化实现，调用基本处理方法
        return self.process_module_file(file_path, output_format)
    
    def save_typescript_file(self, class_info, ts_code, output_dir, filename):
        """
        保存TypeScript文件
        
        Args:
            class_info: 类信息
            ts_code: TypeScript代码
            output_dir: 输出目录
            filename: 文件名
        
        Returns:
            str: 保存的文件路径
        """
        try:
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成文件路径
            if not filename.endswith('.ts'):
                filename = os.path.splitext(filename)[0] + '.ts'
            
            file_path = os.path.join(output_dir, filename)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(ts_code)
            
            self.converted_files.append(file_path)
            return file_path
        except Exception as e:
            print(f"保存TypeScript文件失败 {filename}: {e}")
            return None
    
    def save_javascript_file(self, class_info, js_code, output_dir, filename):
        """
        保存JavaScript文件
        
        Args:
            class_info: 类信息
            js_code: JavaScript代码
            output_dir: 输出目录
            filename: 文件名
        
        Returns:
            str: 保存的文件路径
        """
        try:
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成文件路径
            if not filename.endswith('.js'):
                filename = os.path.splitext(filename)[0] + '.js'
            
            file_path = os.path.join(output_dir, filename)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(js_code)
            
            self.converted_files.append(file_path)
            return file_path
        except Exception as e:
            print(f"保存JavaScript文件失败 {filename}: {e}")
            return None
    
    def _extract_class_info(self, class_body, file_path):
        """
        从类体中提取类信息
        
        Args:
            class_body: 类体内容
            file_path: 文件路径
        
        Returns:
            dict: 类信息
        """
        class_info = {
            'name': 'UnknownClass',
            'extends': 'cc.Component',
            'properties': {},
            'methods': {},
            'file': file_path
        }
        
        # 提取类名
        name_pattern = r'name\s*:\s*["\']([^"\']+)["\']'
        name_match = re.search(name_pattern, class_body)
        if name_match:
            class_info['name'] = name_match.group(1)
        
        # 提取继承关系
        extends_pattern = r'extends\s*:\s*([^,}]+)'
        extends_match = re.search(extends_pattern, class_body)
        if extends_match:
            class_info['extends'] = extends_match.group(1).strip()
        
        # 提取属性
        properties_pattern = r'properties\s*:\s*\{([\s\S]*?)\}\s*(,|\})'
        properties_match = re.search(properties_pattern, class_body)
        if properties_match:
            properties_body = properties_match.group(1)
            class_info['properties'] = self._extract_properties(properties_body)
        
        # 提取方法
        method_pattern = r'(\w+)\s*:\s*function\s*\(([^)]*)\)\s*\{([\s\S]*?)\}'
        method_matches = re.finditer(method_pattern, class_body)
        
        for match in method_matches:
            method_name = match.group(1)
            params = match.group(2)
            method_body = match.group(3)
            
            class_info['methods'][method_name] = {
                'params': [p.strip() for p in params.split(',') if p.strip()],
                'body': method_body.strip()
            }
        
        return class_info
    
    def _extract_properties(self, properties_body):
        """
        提取属性定义
        
        Args:
            properties_body: 属性体内容
        
        Returns:
            dict: 属性字典
        """
        properties = {}
        
        # 简化的属性提取
        prop_pattern = r'(\w+)\s*:\s*([^,}]+)'
        prop_matches = re.finditer(prop_pattern, properties_body)
        
        for match in prop_matches:
            prop_name = match.group(1)
            prop_value = match.group(2).strip()
            
            # 尝试解析属性值
            try:
                if prop_value.startswith('{') and '}' in prop_value:
                    # 对象类型属性
                    prop_value = eval(prop_value)  # 简化处理，实际项目中应使用更安全的解析
                elif prop_value.isdigit():
                    prop_value = int(prop_value)
                elif '.' in prop_value and all(c.isdigit() or c == '.' for c in prop_value):
                    prop_value = float(prop_value)
                elif prop_value.lower() in ['true', 'false']:
                    prop_value = prop_value.lower() == 'true'
            except:
                pass
            
            properties[prop_name] = prop_value
        
        return properties
    
    def _generate_typescript_code(self, class_info):
        """
        生成TypeScript代码
        
        Args:
            class_info: 类信息
        
        Returns:
            str: TypeScript代码
        """
        ts_code = """
// Auto-generated TypeScript class
// From: {file}

cc.Class({{
    name: '{name}',
    extends: {extends},

    properties: {{
{properties}
    }},

{methods}
}});
"""
        
        # 格式化属性
        properties_str = ""
        for prop_name, prop_value in class_info['properties'].items():
            if isinstance(prop_value, dict):
                # 对象类型属性
                prop_str = "        {}: {}".format(prop_name, json.dumps(prop_value, indent=4).replace('\n', '\n        '))
            else:
                # 简单类型属性
                prop_str = "        {}: {}".format(prop_name, prop_value)
            properties_str += prop_str + ",\n"
        
        # 格式化方法
        methods_str = ""
        for method_name, method_info in class_info['methods'].items():
            params_str = ", ".join(method_info['params'])
            method_body = method_info['body'] or "        // TODO: Implement this method"
            methods_str += "    {}({}) {{\n{}\n    }},\n\n".format(
                method_name, params_str, "\n".join(["        " + line for line in method_body.split('\n')])
            )
        
        # 添加默认生命周期方法
        lifecycle_methods = ['onLoad', 'start', 'update', 'lateUpdate', 'onEnable', 'onDisable', 'onDestroy']
        for method_name in lifecycle_methods:
            if method_name not in class_info['methods']:
                if method_name == 'update':
                    methods_str += "    {}() {{\n        // Component update method\n    }},\n\n".format(method_name)
                else:
                    methods_str += "    {}() {{\n        // Component {} method\n    }},\n\n".format(method_name, method_name)
        
        # 填充模板
        ts_code = ts_code.format(
            file=class_info['file'],
            name=class_info['name'],
            extends=class_info['extends'],
            properties=properties_str,
            methods=methods_str
        )
        
        return ts_code
    
    def _generate_javascript_code(self, class_info):
        """
        生成JavaScript代码
        
        Args:
            class_info: 类信息
        
        Returns:
            str: JavaScript代码
        """
        # JavaScript代码生成与TypeScript类似，只是不需要类型注解
        return self._generate_typescript_code(class_info)
