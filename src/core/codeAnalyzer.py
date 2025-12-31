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
            "nodes": []
        }
    
    def analyze(self, code):
        """
        分析代码
        
        Args:
            code (str): JavaScript代码
        """
        from src.utils.logger import logger
        logger().debug("开始分析代码...")
        
        try:
            # 使用esprima解析JavaScript代码
            ast = esprima.parseScript(code, {
                "range": True,
                "loc": True,
                "tolerant": True
            })
            
            # 遍历AST提取cc.Class定义
            self._traverseAST(ast.body)
            
            scripts_count = len(self.analyzed_data["components"])
            logger().info(f"代码分析完成，检测到 {scripts_count} 个cc.Class定义")
            
            # 简单的代码特征提取
            self.analyzed_data["scripts_count"] = scripts_count
            self.analyzed_data["code_length"] = len(code)
        except Exception as e:
            logger().error(f"代码解析失败: {e}")
            # 回退到简单的字符串匹配
            scripts_count = code.count("cc.Class")
            logger().warn(f"使用简单字符串匹配，检测到 {scripts_count} 个cc.Class定义")
            self.analyzed_data["scripts_count"] = scripts_count
            self.analyzed_data["code_length"] = len(code)
    
    def _traverseAST(self, nodes):
        """
        遍历AST节点
        
        Args:
            nodes (list): AST节点列表
        """
        from src.utils.logger import logger
        
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
                                self._extractClassInfo(class_data)
                
                # 递归遍历子节点
                for key, value in node.items():
                    if key != "type" and isinstance(value, (dict, list)):
                        self._traverseAST([value] if isinstance(value, dict) else value)
    
    def _extractClassInfo(self, class_data):
        """
        提取类信息
        
        Args:
            class_data (dict): 类数据AST节点
        """
        from src.utils.logger import logger
        
        if class_data.get("type") == "ObjectExpression":
            class_info = {
                "name": "",
                "extends": "",
                "properties": {}
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
                # 其他属性
                else:
                    class_info["properties"][key_name] = self._extractPropertyValue(prop_value)
            
            logger().info(f"找到cc.Class定义: {class_info['name']} 继承自 {class_info['extends']}")
            self.analyzed_data["components"].append(class_info)
    
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
                if prop_key.get("type") == "Identifier":
                    key_name = prop_key.get("name")
                    obj[key_name] = self._extractPropertyValue(prop_val)
            return obj
        elif value_type == "ArrayExpression":
            arr = []
            for elem in value_node.get("elements", []):
                if elem:
                    arr.append(self._extractPropertyValue(elem))
            return arr
        elif value_type == "FunctionExpression" or value_type == "ArrowFunctionExpression":
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
        else:
            return f"<{value_type}>"
    
    def analyzeMultipleFiles(self, file_paths):
        """
        分析多个文件
        
        Args:
            file_paths (list): 文件路径列表
        """
        from src.utils.logger import logger
        from src.utils.fileManager import fileManager
        
        for file_path in file_paths:
            try:
                logger().info(f"分析文件: {file_path}")
                code = fileManager.readFile(file_path)
                self.analyze(code)
            except Exception as e:
                logger().error(f"分析文件 {file_path} 失败: {e}")
    
    def generateScripts(self, output_path):
        """
        生成脚本文件
        
        Args:
            output_path (str): 输出目录路径
        """
        from src.utils.logger import logger
        from src.utils.fileManager import fileManager
        
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
        
        # 生成脚本内容
        content = f"cc.Class({{\n"
        content += f"    name: '{name}',\n"
        content += f"    extends: {extends},\n"
        
        # 添加属性
        if properties:
            content += "    properties: {\n"
            for prop_name, prop_value in properties.items():
                if isinstance(prop_value, dict):
                    content += f"        {prop_name}: {self._formatValue(prop_value)},\n"
                elif isinstance(prop_value, list):
                    content += f"        {prop_name}: {self._formatValue(prop_value)},\n"
                else:
                    content += f"        {prop_name}: {self._formatValue(prop_value)},\n"
            content += "    },\n"
        
        # 添加默认的生命周期方法
        content += "    \n"
        content += "    onLoad () {\n"
        content += "        // 组件加载时调用\n"
        content += "    },\n"
        content += "    \n"
        content += "    start () {\n"
        content += "        // 组件开始时调用\n"
        content += "    },\n"
        content += "    \n"
        content += "    update (dt) {\n"
        content += "        // 组件更新时调用\n"
        content += "    }\n"
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
            return f"'{value}'"
        elif isinstance(value, dict):
            return "{" + ", ".join([f"{k}: {self._formatValue(v)}" for k, v in value.items()]) + "}"
        elif isinstance(value, list):
            return "[" + ", ".join([self._formatValue(v) for v in value]) + "]"
        elif isinstance(value, bool):
            return str(value).lower()
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
