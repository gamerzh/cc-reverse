#!/usr/bin/env python3
"""
gen_ts.py
Python生成器 - 负责从中间JSON生成TypeScript代码
"""

import json
import os
import argparse

class TypeScriptGenerator:
    """TypeScript代码生成器"""
    
    def __init__(self):
        """初始化生成器"""
        self.input_dir = ""
        self.output_dir = ""
    
    def generate_from_dir(self, input_dir, output_dir, output_format='typescript'):
        """从目录中的所有JSON文件生成代码
        
        Args:
            input_dir: 输入JSON目录
            output_dir: 输出目录
            output_format: 输出格式 (javascript/typescript)
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        
        print("开始从JSON生成代码...")
        print(f"输入目录: {input_dir}")
        print(f"输出目录: {output_dir}")
        print(f"输出格式: {output_format}")
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 处理每个JSON文件
        for fname in os.listdir(input_dir):
            if not fname.endswith(".json"):
                continue
            
            json_path = os.path.join(input_dir, fname)
            self._process_json_file(json_path, output_format)
        
        print("代码生成完成！")
    
    def generate_from_json(self, json_path, output_dir, output_format='typescript'):
        """从单个JSON文件生成代码
        
        Args:
            json_path: JSON文件路径
            output_dir: 输出目录
            output_format: 输出格式 (javascript/typescript)
        """
        self.output_dir = output_dir
        
        print("开始从JSON生成代码...")
        print(f"输入JSON: {json_path}")
        print(f"输出目录: {output_dir}")
        print(f"输出格式: {output_format}")
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 处理JSON文件
        self._process_json_file(json_path, output_format)
        
        print("代码生成完成！")
    
    def _process_json_file(self, json_path, output_format):
        """处理单个JSON文件
        
        Args:
            json_path: JSON文件路径
            output_format: 输出格式
        """
        print(f"处理JSON文件: {json_path}")
        
        # 加载JSON数据
        with open(json_path, 'r', encoding='utf-8') as f:
            modules = json.load(f)
        
        # 处理每个模块
        for mod in modules:
            name = mod["module"]
            imports = mod.get("imports", {})
            props = mod.get("staticProperties", [])
            class_defs = mod.get("classDefinitions", [])
            
            # 生成代码
            if output_format == 'typescript':
                code = self._generate_typescript(name, imports, props, class_defs)
                output_file = os.path.join(self.output_dir, f"{name}.ts")
            else:
                code = self._generate_javascript(name, imports, props, class_defs)
                output_file = os.path.join(self.output_dir, f"{name}.js")
            
            # 写入文件
            with open(output_file, 'w', encoding='utf-8') as out:
                out.write(code)
            
            print(f"生成文件: {output_file}")
    
    def _generate_javascript(self, module_name, imports, static_properties, class_defs):
        """生成JavaScript代码
        
        Args:
            module_name: 模块名
            imports: 导入列表
            static_properties: 静态属性列表
            class_defs: 类定义列表
            
        Returns:
            str: 生成的JavaScript代码
        """
        lines = []
        
        # 1. 文件头注释
        lines.append(f"// 模块名: {module_name}")
        lines.append("")
        
        # 2. 导入语句
        for var, path_ in imports.items():
            base = os.path.basename(path_)
            lines.append(f"var {var} = require('{path_}');")
        
        if imports:
            lines.append("")
        
        # 3. 类定义
        for class_def in class_defs:
            lines.extend(self._generate_js_class(class_def))
            lines.append("")
        
        # 4. 静态属性
        if static_properties:
            lines.append("// 静态属性")
            for p in static_properties:
                lines.append(f"Object.defineProperty(exports, '{p}', {{")
                lines.append(f"  get: function() {{")
                lines.append(f"    // TODO: recovered getter")
                lines.append(f"    return undefined;")
                lines.append(f"  }},")
                lines.append(f"  set: function(v) {{")
                lines.append(f"    // TODO: recovered setter")
                lines.append(f"  }}")
                lines.append(f"}});")
                lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_typescript(self, module_name, imports, static_properties, class_defs):
        """生成TypeScript代码
        
        Args:
            module_name: 模块名
            imports: 导入列表
            static_properties: 静态属性列表
            class_defs: 类定义列表
            
        Returns:
            str: 生成的TypeScript代码
        """
        lines = []
        
        # 1. 文件头注释
        lines.append(f"// 模块名: {module_name}")
        lines.append("")
        
        # 2. 导入语句
        for var, path_ in imports.items():
            base = os.path.basename(path_)
            lines.append(f"import {{ {base} }} from '{path_}';")
        
        if imports:
            lines.append("")
        
        # 3. 类定义
        if class_defs:
            for class_def in class_defs:
                lines.extend(self._generate_ts_class(class_def))
                lines.append("")
        else:
            # 没有类定义，生成一个默认类
            lines.append(f"export class {module_name} {{")
            
            # 4. 静态属性
            for p in static_properties:
                lines.append(f"  static get {p}(): number {{")
                lines.append(f"    // TODO: recovered getter")
                lines.append(f"    return 0;")
                lines.append(f"  }}")
                lines.append("")
                lines.append(f"  static set {p}(v: number) {{")
                lines.append(f"    // TODO: recovered setter")
                lines.append(f"  }}")
                lines.append("")
            
            lines.append(f"}}")
        
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
            
            # 方法
            methods = class_def.get('methods', [])
            for i, method in enumerate(methods):
                lines.extend(self._generate_cc_class_method(method))
                # 添加逗号分隔
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
            class_name = class_def.get('name', 'UnknownClass')
            extends = class_def.get('extends', 'cc.Component')
            lines.append(f"export class {class_name} extends {extends} {{")
            
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
            class_name = class_def.get('name', 'UnknownClass')
            extends = f" extends {class_def.get('extends')}" if class_def.get('extends') else ''
            lines.append(f"export class {class_name}{extends} {{")
            
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
    """命令行入口"""
    parser = argparse.ArgumentParser(description='从JSON生成TypeScript/JavaScript代码')
    parser.add_argument('input', help='输入JSON文件或目录')
    parser.add_argument('output_dir', help='输出目录')
    parser.add_argument('--format', choices=['javascript', 'typescript'], default='typescript', help='输出格式')
    
    args = parser.parse_args()
    
    generator = TypeScriptGenerator()
    
    if os.path.isdir(args.input):
        # 处理目录
        generator.generate_from_dir(args.input, args.output_dir, args.format)
    else:
        # 处理单个文件
        generator.generate_from_json(args.input, args.output_dir, args.format)

if __name__ == '__main__':
    main()