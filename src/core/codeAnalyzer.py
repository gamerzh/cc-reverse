#!/usr/bin/env python3
"""
代码分析器
"""

import os
import esprima

class CodeAnalyzer:
    """代码分析器类"""
    
    def __init__(self):
        """初始化"""
        self.analyzed_data = {
            "scripts": [],
            "resources": [],
            "components": [],
            "nodes": [],
            "dependencies": {}
        }
    
    def analyze(self, code, file_path=""):
        """
        分析代码
        
        Args:
            code (str): JavaScript代码
            file_path (str): 可选的文件路径
        """
        from utils.logger import logger
        logger().debug(f"开始分析代码... 文件: {file_path}")
        
        try:
            # 使用esprima解析JavaScript代码
            ast = esprima.parseScript(code, {
                "range": True,
                "loc": True,
                "tolerant": True
            })
            
            # 遍历AST提取cc.Class定义
            self._traverseAST(ast.body, file_path)
            
            scripts_count = len(self.analyzed_data["components"])
            
            # 如果esprima没有检测到任何组件，使用正则表达式回退
            if scripts_count == 0:
                logger().warn("esprima未检测到组件，使用正则表达式回退分析")
                self._fallbackAnalysis(code, file_path)
                scripts_count = len(self.analyzed_data["components"])
            
            logger().info(f"代码分析完成，检测到 {scripts_count} 个cc.Class定义")
            
            # 简单的代码特征提取
            self.analyzed_data["scripts_count"] = scripts_count
            self.analyzed_data["code_length"] = len(code)
        except Exception as e:
            logger().error(f"代码解析失败: {e}")
            # 回退到更健壮的字符串匹配
            self._fallbackAnalysis(code, file_path)
    
    def _fallbackAnalysis(self, code, file_path=""):
        """
        回退分析方案，使用正则表达式提取cc.Class定义
        
        Args:
            code (str): JavaScript代码
            file_path (str): 可选的文件路径
        """
        from utils.logger import logger
        import re
        
        logger().debug(f"使用正则表达式分析代码... 文件: {file_path}")
        
        # 支持多种Cocos Creator代码模式
        patterns = [
            # 标准cc.Class定义
            r'cc\.Class\s*\(\s*\{([\s\S]*?)\}\s*\)',
            # window.cc.Class定义
            r'window\.cc\.Class\s*\(\s*\{([\s\S]*?)\}\s*\)',
            # 压缩后的代码模式 (function(a,b){return a.Class({...})})
            r'\.Class\s*\(\s*\{([\s\S]*?)\}\s*\)',
        ]
        
        class_matches = []
        for pattern in patterns:
            matches = re.findall(pattern, code)
            if matches:
                class_matches.extend(matches)
                logger().debug(f"模式 {pattern[:30]}... 匹配到 {len(matches)} 个结果")
        
        # 去重
        seen = set()
        unique_matches = []
        for match in class_matches:
            if match not in seen:
                seen.add(match)
                unique_matches.append(match)
        
        scripts_count = len(unique_matches)
        logger().warn(f"使用正则表达式匹配，检测到 {scripts_count} 个cc.Class定义")
        
        for class_match in unique_matches:
            # 尝试提取类名
            name_patterns = [
                r'name\s*:\s*["\']([^"\']+)["\']',
                r'name\s*:\s*([^\s,\}]+)'
            ]
            name_match = None
            for pattern in name_patterns:
                name_match = re.search(pattern, class_match)
                if name_match:
                    break
            
            # 尝试提取继承关系
            extends_patterns = [
                r'extends\s*:\s*["\']([^"\']+)["\']',
                r'extends\s*:\s*([^\s,\}]+)'
            ]
            extends_match = None
            for pattern in extends_patterns:
                extends_match = re.search(pattern, class_match)
                if extends_match:
                    break
            
            class_name = name_match.group(1) if name_match else None
            if class_name:
                class_name = class_name.strip()
                # 跳过非类名（如数字、特殊字符）
                if not class_name or class_name[0].isdigit():
                    class_name = f"Unknown_{len(self.analyzed_data['components'])}"
            else:
                class_name = f"Unknown_{len(self.analyzed_data['components'])}"
            
            class_info = {
                "name": class_name,
                "extends": extends_match.group(1).strip() if extends_match else "cc.Component",
                "properties": {},
                "methods": {}
            }
            
            self.analyzed_data["components"].append(class_info)
            logger().info(f"提取到组件: {class_info['name']} 继承自 {class_info['extends']}")
        
        self.analyzed_data["scripts_count"] = scripts_count
        self.analyzed_data["code_length"] = len(code)
    
    def _traverseAST(self, nodes, file_path=""):
        """
        遍历AST节点
        
        Args:
            nodes (list): AST节点列表
            file_path (str): 可选的文件路径
        """
        from utils.logger import logger
        
        for node in nodes:
            if isinstance(node, dict):
                node_type = node.get("type")
                
                # 查找cc.Class调用表达式
                if node_type == "ExpressionStatement":
                    expr = node.get("expression")
                    if expr and expr.get("type") == "CallExpression":
                        callee = expr.get("callee")
                        # 检查是否是 cc.Class 调用
                        if (callee and callee.get("type") == "MemberExpression" and 
                            callee.get("object", {}).get("name") == "cc" and 
                            callee.get("property", {}).get("name") == "Class"):
                            # 提取cc.Class的参数
                            args = expr.get("arguments", [])
                            if args:
                                class_data = args[0]
                                self._extractClassInfo(class_data, file_path)
                
                # 递归遍历子节点
                for key, value in node.items():
                    if key != "type" and isinstance(value, (dict, list)):
                        self._traverseAST([value] if isinstance(value, dict) else value, file_path)
    
    def _extractClassInfo(self, class_data, file_path=""):
        """
        提取类信息
        
        Args:
            class_data (dict): 类数据AST节点
            file_path (str): 可选的文件路径
        """
        from src.utils.logger import logger
        
        if class_data.get("type") == "ObjectExpression":
            class_info = {
                "name": "",
                "extends": "",
                "properties": {},
                "methods": {},
                "statics": {},
                "mixins": [],
                "file_path": file_path
            }
            
            # 提取类的属性
            properties = class_data.get("properties", [])
            for prop in properties:
                prop_key = prop.get("key", {})
                prop_value = prop.get("value", {})
                
                # 处理不同类型的属性键
                if prop_key.get("type") == "Identifier":
                    key_name = prop_key.get("name")
                elif prop_key.get("type") == "Literal":
                    key_name = prop_key.get("value")
                else:
                    continue
                
                # 处理类名
                if key_name == "name" and prop_value.get("type") == "Literal":
                    class_info["name"] = prop_value.get("value")
                # 处理继承关系
                elif key_name == "extends" and prop_value.get("type") == "MemberExpression":
                    extends_path = []
                    curr = prop_value
                    while curr:
                        if curr.get("property", {}).get("name"):
                            extends_path.insert(0, curr.get("property").get("name"))
                        curr = curr.get("object")
                        if curr and curr.get("type") == "Identifier":
                            extends_path.insert(0, curr.get("name"))
                            break
                    class_info["extends"] = ".".join(extends_path)
                # 处理属性
                elif key_name == "properties" and prop_value.get("type") == "ObjectExpression":
                    # 提取属性定义
                    for prop_def in prop_value.get("properties", []):
                        prop_def_key = prop_def.get("key", {})
                        prop_def_value = prop_def.get("value", {})
                        
                        if prop_def_key.get("type") == "Identifier":
                            prop_name = prop_def_key.get("name")
                            class_info["properties"][prop_name] = self._extractPropertyValue(prop_def_value)
                # 处理静态属性
                elif key_name == "statics" and prop_value.get("type") == "ObjectExpression":
                    # 提取静态属性定义
                    for static_def in prop_value.get("properties", []):
                        static_def_key = static_def.get("key", {})
                        static_def_value = static_def.get("value", {})
                        
                        if static_def_key.get("type") == "Identifier":
                            static_name = static_def_key.get("name")
                            class_info["statics"][static_name] = self._extractPropertyValue(static_def_value)
                # 处理混入
                elif key_name == "mixins" and prop_value.get("type") == "ArrayExpression":
                    for mixin in prop_value.get("elements", []):
                        if mixin and mixin.get("type") == "Identifier":
                            class_info["mixins"].append(mixin.get("name"))
                # 处理方法
                else:
                    # 检查是否是方法定义
                    if prop_value.get("type") in ["FunctionExpression", "ArrowFunctionExpression"]:
                        class_info["methods"][key_name] = self._extractMethodInfo(prop_value)
                    else:
                        # 其他顶层属性
                        class_info[key_name] = self._extractPropertyValue(prop_value)
            
            if class_info["name"]:
                logger().info(f"找到cc.Class定义: {class_info['name']} 继承自 {class_info['extends']}")
                self.analyzed_data["components"].append(class_info)
    
    def _extractMethodInfo(self, method_node):
        """
        提取方法信息
        
        Args:
            method_node (dict): 方法的AST节点
        
        Returns:
            dict: 方法信息
        """
        method_info = {
            "params": [],
            "is_arrow": method_node.get("type") == "ArrowFunctionExpression"
        }
        
        # 提取参数
        if method_node.get("params"):
            for param in method_node.get("params"):
                if param.get("type") == "Identifier":
                    method_info["params"].append(param.get("name"))
        
        return method_info
    
    def _extractPropertyValue(self, value_node):
        """
        提取属性值
        
        Args:
            value_node (dict): 值的AST节点
        
        Returns:
            any: 提取的值
        """
        value_type = value_node.get("type")
        
        if value_type == "Literal":
            return value_node.get("value")
        elif value_type == "ObjectExpression":
            obj = {}
            for prop in value_node.get("properties", []):
                prop_key = prop.get("key")
                prop_val = prop.get("value")
                if prop_key:
                    if prop_key.get("type") == "Identifier":
                        key_name = prop_key.get("name")
                    elif prop_key.get("type") == "Literal":
                        key_name = prop_key.get("value")
                    else:
                        continue
                    obj[key_name] = self._extractPropertyValue(prop_val)
            return obj
        elif value_type == "ArrayExpression":
            arr = []
            for elem in value_node.get("elements", []):
                if elem:
                    arr.append(self._extractPropertyValue(elem))
            return arr
        elif value_type in ["FunctionExpression", "ArrowFunctionExpression"]:
            return "function"
        elif value_type == "MemberExpression":
            # 处理 cc.Sprite 这样的成员表达式
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
        elif value_type == "Identifier":
            return value_node.get("name")
        elif value_type == "UnaryExpression":
            # 处理布尔值和数字的一元表达式
            operator = value_node.get("operator")
            argument = self._extractPropertyValue(value_node.get("argument"))
            if operator == "!":
                return not argument
            elif operator == "-":
                return -argument
            return f"{operator}{argument}"
        else:
            return f"<{value_type}>"
    
    def analyzeMultipleFiles(self, file_paths):
        """
        分析多个文件
        
        Args:
            file_paths (list): 文件路径列表
        """
        from utils.logger import logger
        from utils.fileManager import fileManager
        
        for file_path in file_paths:
            try:
                logger().info(f"分析文件: {file_path}")
                code = fileManager.readFile(file_path)
                self.analyze(code, file_path)
            except Exception as e:
                logger().error(f"分析文件 {file_path} 失败: {e}")
    
    def generateScripts(self, output_path):
        """
        生成脚本文件
        
        Args:
            output_path (str): 输出目录路径
        """
        from src.utils.logger import logger
        from utils.fileManager import fileManager
        
        logger().info(f"生成脚本文件到: {output_path}")
        
        # 确保输出目录存在
        scripts_dir = os.path.join(output_path, "assets", "scripts")
        os.makedirs(scripts_dir, exist_ok=True)
        
        # 生成每个组件的脚本文件
        for component in self.analyzed_data["components"]:
            script_content = self._generateScriptContent(component)
            script_name = component.get("name", "Unknown") + ".js"
            script_path = os.path.join(scripts_dir, script_name)
            
            fileManager.writeFile(script_path, script_content)
            logger().info(f"生成脚本: {script_path}")
    
    def _generateScriptContent(self, component):
        """
        生成脚本内容
        
        Args:
            component (dict): 组件信息
        
        Returns:
            str: 脚本内容
        """
        name = component.get("name", "UnknownComponent")
        extends = component.get("extends", "cc.Component")
        properties = component.get("properties", {})
        methods = component.get("methods", {})
        statics = component.get("statics", {})
        mixins = component.get("mixins", [])
        
        # 生成脚本内容
        content = f"cc.Class({{\n"
        content += f"    name: '{name}',\n"
        content += f"    extends: {extends},\n"
        
        # 添加混入
        if mixins:
            content += f"    mixins: [{', '.join(mixins)}],\n"
        
        # 添加静态属性
        if statics:
            content += "    statics: {\n"
            for stat_name, stat_value in statics.items():
                content += f"        {stat_name}: {self._formatValue(stat_value)},\n"
            content = content.rstrip(",\n") + "\n    },\n"
        
        # 添加属性
        if properties:
            content += "    properties: {\n"
            for prop_name, prop_value in properties.items():
                content += f"        {prop_name}: {self._formatValue(prop_value)},\n"
            content = content.rstrip(",\n") + "\n    },\n"
        
        # 添加其他顶层属性
        other_props = [key for key in component.keys() if key not in ["name", "extends", "properties", "methods", "statics", "mixins", "file_path"]]
        if other_props:
            for prop_key in other_props:
                prop_value = component[prop_key]
                if prop_value is not None:
                    content += f"    {prop_key}: {self._formatValue(prop_value)},\n"
        
        # 添加方法
        if methods:
            for method_name, method_info in methods.items():
                params = ", ".join(method_info["params"])
                content += f"    {method_name} ({params}) {{\n"
                content += f"        // 自动生成的方法\n"
                content += f"    }},\n"
        
        # 添加默认的生命周期方法（如果没有定义）
        lifecycle_methods = ["onLoad", "start", "update", "lateUpdate", "onEnable", "onDisable", "onDestroy"]
        for lifecycle_method in lifecycle_methods:
            if lifecycle_method not in methods:
                if lifecycle_method == "update":
                    content += f"    {lifecycle_method} (dt) {{\n"
                    content += f"        // 组件更新时调用\n"
                    content += f"    }},\n"
                else:
                    content += f"    {lifecycle_method} () {{\n"
                    content += f"        // {lifecycle_method} 生命周期方法\n"
                    content += f"    }},\n"
        
        # 移除最后一个逗号
        if content.endswith(",\n"):
            content = content[:-2] + "\n"
        
        content += "}\n);"
        
        return content
    
    def _formatValue(self, value):
        """
        格式化值为JavaScript字符串
        
        Args:
            value: 要格式化的值
        
        Returns:
            str: 格式化后的字符串
        """
        if isinstance(value, str):
            # 转义特殊字符
            escaped_value = value.replace("'", "\\'")
            return f"'{escaped_value}'"
        elif isinstance(value, dict):
            # 确保属性值正确格式化
            props = []
            for k, v in value.items():
                # 处理特殊属性，如 default, type, visible 等
                if k == "type" and isinstance(v, str) and "." in v:
                    props.append(f"{k}: {v}")
                else:
                    props.append(f"{k}: {self._formatValue(v)}")
            return "{" + ", ".join(props) + "}"
        elif isinstance(value, list):
            return "[" + ", ".join([self._formatValue(v) for v in value]) + "]"
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, type(None)):
            return "null"
        else:
            return str(value)
    
    def getData(self):
        """
        获取分析后的数据
        
        Returns:
            dict: 分析后的数据
        """
        return self.analyzed_data

# 创建全局实例
codeAnalyzer = CodeAnalyzer()
