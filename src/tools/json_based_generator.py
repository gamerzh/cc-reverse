#!/usr/bin/env python3
"""
基于JSON中间格式的代码生成器

架构：
[Node.js] -> 分析代码 -> 生成中间JSON
        ↓
[Python] -> 读取JSON -> 生成最终代码
"""

import json
import os
import re

class JSONBasedGenerator:
    """基于JSON中间格式的代码生成器"""
    
    def __init__(self):
        """初始化"""
        self.output_dir = ""
    
    def load_json(self, json_path):
        """加载中间JSON文件
        
        Args:
            json_path: JSON文件路径
            
        Returns:
            dict: JSON数据
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def generate_code_from_json(self, json_path, output_dir, output_format='javascript'):
        """从JSON生成代码
        
        Args:
            json_path: JSON文件路径
            output_dir: 输出目录
            output_format: 输出格式，'javascript' 或 'typescript'
        """
        self.output_dir = output_dir
        
        # 1. 加载JSON数据
        data = self.load_json(json_path)
        
        # 2. 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 3. 处理每个分析结果
        for result in data.get('results', []):
            if not result.get('success'):
                print(f"跳过失败的结果: {result.get('filePath')}")
                continue
            
            self._process_analysis_result(result, output_format)
    
    def _process_analysis_result(self, result, output_format):
        """处理单个分析结果
        
        Args:
            result: 分析结果
            output_format: 输出格式
        """
        analysis_data = result.get('data', {})
        file_path = analysis_data.get('filePath', '')
        file_name = analysis_data.get('fileName', '')
        
        print(f"处理文件: {file_path}")
        
        # 4. 生成代码
        if output_format == 'typescript':
            code = self._generate_typescript(analysis_data)
            output_file = os.path.join(self.output_dir, os.path.splitext(file_name)[0] + '.ts')
        else:
            code = self._generate_javascript(analysis_data)
            output_file = os.path.join(self.output_dir, os.path.splitext(file_name)[0] + '.js')
        
        # 5. 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        print(f"生成文件: {output_file}")
    
    def _generate_javascript(self, analysis_data):
        """生成JavaScript代码
        
        Args:
            analysis_data: 分析数据
            
        Returns:
            str: 生成的JavaScript代码
        """
        lines = []
        
        # 1. 文件头注释
        lines.append(f"// 生成自: {analysis_data.get('fileName')}")
        lines.append(f"// 模块名: {analysis_data.get('moduleName')}")
        lines.append("")
        
        # 2. 导入语句（简化处理）
        dependencies = analysis_data.get('dependencies', [])
        if dependencies:
            for dep in dependencies:
                lines.append(f"// import {dep['name']} from '{dep['path']}';")
            lines.append("")
        
        # 3. 类定义
        class_defs = analysis_data.get('classDefinitions', [])
        if class_defs:
            for class_def in class_defs:
                lines.extend(self._generate_js_class(class_def))
                lines.append("")
        
        # 4. 静态字段
        static_fields = analysis_data.get('staticFields', [])
        if static_fields:
            lines.append("// 静态字段")
            for field in static_fields:
                lines.append(f"{field['name']} = {field['value']};")
            lines.append("")
        
        # 5. 方法定义
        methods = analysis_data.get('methods', [])
        if methods:
            lines.append("// 全局方法")
            for method in methods:
                lines.extend(self._generate_js_method(method))
                lines.append("")
        
        # 6. 使用Prettier美化的原始代码（可选）
        prettified = analysis_data.get('prettifiedContent', '')
        if prettified and not class_defs:
            lines.append("// 原始代码（已美化）")
            lines.append(prettified)
        
        return '\n'.join(lines)
    
    def _generate_js_class(self, class_def):
        """生成JavaScript类定义
        
        Args:
            class_def: 类定义数据
            
        Returns:
            list: 类定义行列表
        """
        lines = []
        
        if class_def['type'] == 'cc_class':
            # 生成cc.Class定义
            lines.append(f"cc.Class({{")
            lines.append(f"  name: '{class_def.get('name', 'UnknownClass')}',")
            lines.append(f"  extends: {class_def.get('extends', 'cc.Component')},")
            
            # 属性
            props = class_def.get('properties', [])
            if props:
                lines.append("  properties: {")
                for prop in props:
                    lines.append(f"    {prop['name']}: {self._generate_property_def(prop)},")
                lines.append("  },")
            
            # 静态属性
            statics = class_def.get('statics', [])
            if statics:
                lines.append("  statics: {")
                for prop in statics:
                    lines.append(f"    {prop['name']}: {self._generate_property_def(prop)},")
                lines.append("  },")
            
            # 方法
            methods = class_def.get('methods', [])
            for i, method in enumerate(methods):
                lines.extend(self._generate_cc_class_method(method))
                # 添加逗号分隔（最后一个方法除外）
                if i < len(methods) - 1:
                    lines[-1] = lines[-1] + ','
            
            lines.append("});")
        elif class_def['type'] == 'es6_class':
            # 生成ES6类定义
            extends = f" extends {class_def.get('extends')}" if class_def.get('extends') else ''
            lines.append(f"class {class_def.get('name', 'UnknownClass')}{extends} {{")
            
            # 方法
            methods = class_def.get('methods', [])
            for method in methods:
                lines.extend(self._generate_es6_class_method(method))
            
            lines.append("}")
        
        return lines
    
    def _generate_typescript(self, analysis_data):
        """生成TypeScript代码
        
        Args:
            analysis_data: 分析数据
            
        Returns:
            str: 生成的TypeScript代码
        """
        lines = []
        
        # 1. 文件头注释
        lines.append(f"// 生成自: {analysis_data.get('fileName')}")
        lines.append(f"// 模块名: {analysis_data.get('moduleName')}")
        lines.append("")
        
        # 2. 导入语句
        dependencies = analysis_data.get('dependencies', [])
        if dependencies:
            for dep in dependencies:
                lines.append(f"import {{ {dep['name']} }} from '{dep['path']}';")
            lines.append("")
        
        # 3. 类定义
        class_defs = analysis_data.get('classDefinitions', [])
        if class_defs:
            for class_def in class_defs:
                lines.extend(self._generate_ts_class(class_def))
                lines.append("")
        else:
            # 没有类定义，生成默认类
            module_name = analysis_data.get('moduleName', os.path.splitext(analysis_data.get('fileName', ''))[0])
            lines.append(f"export class {module_name} {{")
            lines.append(f"  // 自动生成的类")
            lines.append(f"}}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_ts_class(self, class_def):
        """生成TypeScript类定义
        
        Args:
            class_def: 类定义数据
            
        Returns:
            list: 类定义行列表
        """
        lines = []
        
        if class_def['type'] == 'cc_class':
            # 生成cc.Class的TypeScript版本
            lines.append(f"export class {class_def.get('name', 'UnknownClass')} extends {class_def.get('extends', 'cc.Component')} {{")
            
            # 属性
            props = class_def.get('properties', [])
            for prop in props:
                ts_type = prop.get('type', 'any')
                lines.append(f"  {prop['name']}: {ts_type};")
            
            # 方法
            methods = class_def.get('methods', [])
            for method in methods:
                params_str = ', '.join([f"{param}: any" for param in method.get('params', [])])
                lines.append(f"  {method['name']}({params_str}): void {{")
                lines.append(f"    // 方法实现")
                lines.append(f"  }}")
            
            lines.append(f"}}")
        elif class_def['type'] == 'es6_class':
            # 生成ES6类的TypeScript版本
            extends = f" extends {class_def.get('extends')}" if class_def.get('extends') else ''
            lines.append(f"export class {class_def.get('name', 'UnknownClass')}{extends} {{")
            
            # 方法
            methods = class_def.get('methods', [])
            for method in methods:
                params_str = ', '.join([f"{param}: any" for param in method.get('params', [])])
                lines.append(f"  {method['name']}({params_str}): void {{")
                lines.append(f"    // 方法实现")
                lines.append(f"  }}")
            
            lines.append(f"}}")
        
        return lines
    
    def _generate_property_def(self, prop):
        """生成属性定义
        
        Args:
            prop: 属性数据
            
        Returns:
            str: 属性定义字符串
        """
        if prop.get('defaultValue') is not None:
            if isinstance(prop['defaultValue'], str):
                return f"{{ default: '{prop['defaultValue']}', type: {prop['type']} }}"
            return f"{{ default: {prop['defaultValue']}, type: {prop['type']} }}"
        return f"{{ type: {prop['type']} }}"
    
    def _generate_js_method(self, method):
        """生成JavaScript方法
        
        Args:
            method: 方法数据
            
        Returns:
            list: 方法定义行列表
        """
        params_str = ', '.join(method.get('params', []))
        lines = []
        lines.append(f"function {method['name']}({params_str}) {{")
        lines.append(f"  // 方法实现")
        lines.append(f"}}")
        return lines
    
    def _generate_cc_class_method(self, method):
        """生成cc.Class中的方法
        
        Args:
            method: 方法数据
            
        Returns:
            list: 方法定义行列表
        """
        params_str = ', '.join(method.get('params', []))
        return [
            f"  {method['name']}: function({params_str}) {{",
            f"    // 方法实现",
            f"  }}"
        ]
    
    def _generate_es6_class_method(self, method):
        """生成ES6类中的方法
        
        Args:
            method: 方法数据
            
        Returns:
            list: 方法定义行列表
        """
        params_str = ', '.join(method.get('params', []))
        return [
            f"  {method['name']}({params_str}) {{",
            f"    // 方法实现",
            f"  }}"
        ]


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='基于JSON的代码生成器')
    parser.add_argument('json_path', help='中间JSON文件路径')
    parser.add_argument('output_dir', help='输出目录')
    parser.add_argument('--format', choices=['javascript', 'typescript'], default='javascript', help='输出格式')
    
    args = parser.parse_args()
    
    generator = JSONBasedGenerator()
    generator.generate_code_from_json(args.json_path, args.output_dir, args.format)


if __name__ == '__main__':
    main()