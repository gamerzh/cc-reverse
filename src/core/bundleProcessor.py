#!/usr/bin/env python3
"""
bundle文件处理器 - 处理Webpack打包的JavaScript bundle文件
"""

import os
import re
import sys
import json
import shutil
from pathlib import Path

# 导入项目工具
from utils.logger import logger
from utils.fileManager import fileManager

# 导入外部工具
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 尝试导入bundle_extractor和module_converter
try:
    from src.tools import bundle_extractor
    from src.tools import module_converter
    EXTERNAL_TOOLS_AVAILABLE = True
except ImportError as e:
    logger().warn(f"无法导入外部工具: {e}")
    EXTERNAL_TOOLS_AVAILABLE = False

class BundleProcessor:
    """bundle文件处理器"""
    
    def __init__(self):
        self.extracted_modules = {}
        self.converted_classes = []
    
    def is_webpack_bundle(self, file_path):
        """检查文件是否为Webpack打包的bundle"""
        try:
            content = fileManager.readFile(file_path)
            # Webpack bundle的常见特征
            webpack_patterns = [
                r'window\.__require\s*=\s*function',
                r'\(window\s*,\s*document\)',
                r'function\(e,t,o\)',
                r'cc\._RF\.push',
                r'this&&this\.__extends',
                r'this&&this\.__decorate',
                r'Object\.defineProperty\(o,"__esModule"',
            ]
            
            for pattern in webpack_patterns:
                if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                    return True
            
            # 检查是否包含模块定义
            if 'webpackJsonp' in content or 'webpackChunk' in content:
                return True
                
            return False
        except Exception as e:
            logger().warn(f"检查bundle文件失败 {file_path}: {e}")
            return False
    
    def extract_bundle_modules(self, bundle_path, output_dir=None):
        """
        从bundle文件中提取模块
        
        Args:
            bundle_path: bundle文件路径
            output_dir: 输出目录（如果不指定，则在bundle所在目录下创建script目录）
        
        Returns:
            dict: 提取的模块信息
        """
        from utils.logger import logger
        
        logger().info(f"提取bundle: {bundle_path}")
        
        # 如果未指定输出目录，则在bundle所在目录下创建script目录
        if output_dir is None:
            bundle_dir = os.path.dirname(bundle_path)
            output_dir = os.path.join(bundle_dir, "script")
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # 使用bundle_extractor提取模块
            saved_count, extracted_output_dir = bundle_extractor.extract_bundle(bundle_path, output_dir)
            
            if saved_count == 0:
                logger().warn(f"未从 {bundle_path} 提取到任何模块")
                return {}
            
            # 获取保存的模块文件列表
            saved_modules = []
            for item in os.listdir(extracted_output_dir):
                if item.endswith('.js'):
                    saved_modules.append(item)
            
            logger().success(f"从 {os.path.basename(bundle_path)} 成功提取 {len(saved_modules)} 个模块到 {extracted_output_dir}")
            
            # 记录提取信息
            bundle_name = os.path.basename(bundle_path)
            self.extracted_modules[bundle_name] = {
                'path': bundle_path,
                'output_dir': extracted_output_dir,
                'modules_count': len(saved_modules),
                'modules': saved_modules
            }
            
            return self.extracted_modules[bundle_name]
            
        except Exception as e:
            logger().error(f"提取bundle失败 {bundle_path}: {e}")
            return {}
    
    def _extract_modules_from_bundle(self, content):
        """
        从bundle内容中提取模块
        
        这是简化的提取逻辑，实际可能需要更复杂的解析
        """
        modules = {}
        
        # 查找Webpack模块定义
        # 模式: window.__require=function(e){var t={};function o(r){if(t[r])return t[r].exports;var n=t[r]={i:r,l:!1,exports:{}};...
        # 或: (function(e){var t={};function o(r){if(t[r])return t[r].exports;var n=t[r]={i:r,l:!1,exports:{}};...
        
        # 简化版本：查找所有类似 function(e,t,o) 的模块定义
        module_pattern = r'function\s*\([^)]*\)\s*\{[^}]*?"use strict";[^}]*?cc\._RF\.push\([^,]+,\s*"[^"]+",\s*"([^"]+)"\)[^}]*?\}'
        
        matches = re.finditer(module_pattern, content, re.DOTALL)
        
        for i, match in enumerate(matches):
            module_name = match.group(1) if match.group(1) else f"module_{i}"
            module_code = match.group(0)
            
            # 提取依赖信息（简化版本）
            dependencies = {}
            # 查找模块参数中的依赖：function(e,t,o){...} 其中e,t,o对应依赖
            # 实际需要更复杂的解析
            
            modules[i] = {
                'id': i,
                'name': module_name,
                'code': module_code,
                'dependencies': dependencies
            }
        
        # 如果没有找到使用上述模式，尝试查找其他模式
        if not modules:
            # 备用模式：查找包含cc._RF.push的代码块
            alt_pattern = r'cc\._RF\.push\([^,]+,\s*"[^"]+",\s*"([^"]+)"\)[^}]*?\}'
            alt_matches = re.finditer(alt_pattern, content, re.DOTALL)
            
            for i, match in enumerate(alt_matches):
                module_name = match.group(1) if match.group(1) else f"module_{i}"
                # 获取更大范围的代码
                start = max(0, match.start() - 500)
                end = min(len(content), match.end() + 500)
                module_code = content[start:end]
                
                modules[i] = {
                    'id': i,
                    'name': module_name,
                    'code': module_code,
                    'dependencies': {}
                }
        
        return modules
    
    def _build_module_content(self, module_info, bundle_path):
        """构建模块文件内容"""
        bundle_name = os.path.basename(bundle_path)
        module_name = module_info.get('name', 'Unknown')
        
        content = f"// 模块: {module_name}\n"
        content += f"// 来自bundle: {bundle_name}\n"
        
        # 添加依赖信息
        deps = module_info.get('dependencies', {})
        if deps:
            content += f"// 依赖: {json.dumps(deps, ensure_ascii=False)}\n"
        
        content += "\n"
        content += module_info.get('code', '')
        
        return content
    
    def convert_modules_to_typescript(self, extracted_info, output_dir=None, format='javascript'):
        """
        将提取的模块转换为指定格式的代码（默认JavaScript）
        
        Args:
            extracted_info: 从extract_bundle_modules返回的信息
            output_dir: 输出目录
            format: 输出格式，'javascript' 或 'typescript'
        
        Returns:
            list: 转换后的类信息
        """
        from utils.logger import logger
        
        if not extracted_info:
            logger().warn("没有可转换的模块信息")
            return []
        
        modules_dir = extracted_info.get('output_dir')
        if not modules_dir or not os.path.exists(modules_dir):
            logger().error(f"模块目录不存在: {modules_dir}")
            return []
        
        # 如果未指定输出目录，则根据格式处理
        if output_dir is None:
            if format == 'javascript':
                # JavaScript模式：直接覆盖原始script目录下的文件
                output_dir = modules_dir
            else:  # typescript
                # TypeScript模式：在script目录下创建typescript子目录
                output_dir = os.path.join(modules_dir, "typescript")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取所有.js文件
        js_files = []
        for item in os.listdir(modules_dir):
            if item.endswith('.js'):
                js_files.append(os.path.join(modules_dir, item))
        
        if not js_files:
            logger().warn(f"模块目录中没有找到.js文件: {modules_dir}")
            return []
        
        logger().info(f"开始转换 {len(js_files)} 个模块为{format}...")
        
        converted_classes = []
        
        # 创建ModuleConverter实例
        converter = module_converter.ModuleConverter()
        
        # 处理每个.js文件
        for js_file in js_files:
            try:
                results = converter.process_module_file(js_file, output_format=format)
                
                if results:
                    # 如果同一个文件中有多个类，为每个类生成不同的文件名
                    for idx, result in enumerate(results):
                        # 根据格式保存文件
                        if format == 'javascript':
                            code_key = 'js_code'
                            # 如果有多个类，在文件名后添加索引
                            if len(results) > 1:
                                base_name = os.path.splitext(os.path.basename(js_file))[0]
                                class_name = result['class_info'].get('name', f'Class_{idx+1}')
                                safe_class_name = re.sub(r'[\\/*?:"<>|]', '_', class_name)
                                filename = f"{base_name}_{safe_class_name}.js"
                            else:
                                filename = os.path.basename(js_file)
                            
                            output_path = converter.save_javascript_file(
                                result['class_info'], 
                                result['js_code'], 
                                output_dir,
                                filename
                            )
                        else:  # typescript
                            code_key = 'ts_code'
                            # 如果有多个类，在文件名后添加索引
                            if len(results) > 1:
                                base_name = os.path.splitext(os.path.basename(js_file))[0]
                                class_name = result['class_info'].get('name', f'Class_{idx+1}')
                                safe_class_name = re.sub(r'[\\/*?:"<>|]', '_', class_name)
                                filename = f"{base_name}_{safe_class_name}.ts"
                            else:
                                filename = os.path.basename(js_file)
                            
                            output_path = converter.save_typescript_file(
                                result['class_info'], 
                                result['ts_code'], 
                                output_dir,
                                filename
                            )
                        
                        if output_path:
                            converted_classes.append({
                                'original_file': js_file,
                                'ts_file': output_path,
                                'class_info': result['class_info']
                            })
                            
                            logger().debug(f"转换: {os.path.basename(js_file)} -> {os.path.basename(output_path)}")
                else:
                    logger().debug(f"未从 {os.path.basename(js_file)} 提取到类信息")
            except Exception as e:
                logger().error(f"转换模块失败 {js_file}: {e}")
        
        logger().success(f"成功转换 {len(converted_classes)} 个类为{format}到 {output_dir}")
        
        self.converted_classes.extend(converted_classes)
        return converted_classes
    
    def _extract_class_from_module(self, content, file_path):
        """从模块内容中提取类信息（简化版本）"""
        # 这里可以使用现有的module_converter中的逻辑
        # 暂时使用简化版本
        
        class_info = {
            'name': 'UnknownClass',
            'extends': 'cc.Component',
            'properties': {},
            'methods': {},
            'file': file_path
        }
        
        # 提取类名
        name_patterns = [
            r'cc\._RF\.push\([^,]+,\s*"[^"]+",\s*"([^"]+)"\)',
            r'o\.(\w+)\s*=',
            r't\.exports\s*=\s*(\w+)',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, content)
            if match and match.group(1):
                class_info['name'] = match.group(1)
                break
        
        # 查找装饰器类
        decorator_pattern = r'(i|r)\(\[([^\]]+)\],\s*(\w+)\)\}\(([^)]+)\)'
        decorator_match = re.search(decorator_pattern, content)
        
        if decorator_match:
            class_info['name'] = decorator_match.group(3)
            class_info['extends'] = decorator_match.group(4)
            # 解析装饰器
            decorators = decorator_match.group(2).split(',')
            class_info['decorators'] = [d.strip() for d in decorators if d.strip()]
        
        # 查找cc.Class定义
        ccclass_pattern = r'cc\.Class\s*\(\s*\{([\s\S]*?)\}\s*\)'
        ccclass_match = re.search(ccclass_pattern, content)
        
        if ccclass_match:
            class_body = ccclass_match.group(1)
            # 解析cc.Class体
            self._parse_cc_class_body(class_body, class_info)
        
        return class_info
    
    def _parse_cc_class_body(self, class_body, class_info):
        """解析cc.Class体（改进版本）"""
        # 提取类名
        name_pattern = r'name\s*:\s*["\']([^"\']+)["\']'
        name_match = re.search(name_pattern, class_body)
        if name_match:
            class_info['name'] = name_match.group(1)
        
        # 提取继承关系
        extends_pattern = r'extends\s*:\s*["\']([^"\']+)["\']'
        extends_match = re.search(extends_pattern, class_body)
        if extends_match:
            class_info['extends'] = extends_match.group(1)
        
        # 尝试提取属性
        properties_pattern = r'properties\s*:\s*\{([\s\S]*?)\}(?=\s*[,}])'
        properties_match = re.search(properties_pattern, class_body)
        if properties_match:
            properties_str = properties_match.group(1)
            # 简单解析属性键值对
            prop_pattern = r'(\w+)\s*:\s*({[^}]+}|\[[^\]]+\]|[^,}]+)'
            prop_matches = re.findall(prop_pattern, properties_str)
            for prop_name, prop_value in prop_matches:
                class_info.setdefault('properties', {})[prop_name.strip()] = prop_value.strip()
        
        # 尝试提取方法
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
                
                class_info.setdefault('methods', {})[method_name] = {
                    'params': [p.strip() for p in params.split(',') if p.strip()],
                    'body': method_body.strip()
                }
        
        return class_info
    
    def _generate_typescript(self, class_info):
        """生成TypeScript代码（简化版本）"""
        ts_code = ""
        
        # 添加装饰器
        decorators = class_info.get('decorators', [])
        for decorator in decorators:
            if 'ccclass' in decorator.lower():
                ts_code += f"@ccclass\n"
            elif 'property' in decorator.lower():
                ts_code += f"@property\n"
            else:
                ts_code += f"@{decorator}\n"
        
        # 添加类定义
        ts_code += f"export class {class_info['name']} extends {class_info['extends']} {{\n"
        
        # 添加属性
        for prop_name, prop_type in class_info.get('properties', {}).items():
            ts_code += f"    {prop_name}: {prop_type};\n"
        
        if class_info.get('properties'):
            ts_code += "\n"
        
        # 添加方法占位符
        for method_name in class_info.get('methods', {}).keys():
            ts_code += f"    {method_name}() {{\n"
            ts_code += f"        // 方法实现\n"
            ts_code += f"    }}\n\n"
        
        ts_code += "}\n"
        return ts_code
    
    def process_bundle_file(self, bundle_path, output_base_dir, res_path):
        """
        完整处理一个bundle文件
        
        Args:
            bundle_path: bundle文件路径
            output_base_dir: 基础输出目录
            res_path: 资源目录路径，用于计算相对路径
        
        Returns:
            dict: 处理结果
        """
        from utils.logger import logger
        
        logger().info(f"开始完整处理bundle文件: {bundle_path}")
        
        # 确定输出目录结构
        bundle_dir = os.path.dirname(bundle_path)
        bundle_name = os.path.basename(bundle_path)
        
        # 计算bundle目录相对于资源目录的路径
        # 在输出目录中创建对应的bundle目录结构
        rel_path = os.path.relpath(bundle_dir, res_path)
        bundle_output_dir = os.path.join(output_base_dir, rel_path)
        logger().debug(f"bundle_dir: {bundle_dir}")
        logger().debug(f"res_path: {res_path}")
        logger().debug(f"rel_path: {rel_path}")
        logger().debug(f"output_base_dir: {output_base_dir}")
        logger().debug(f"bundle_output_dir: {bundle_output_dir}")
        
        # 提取模块
        extraction_result = self.extract_bundle_modules(bundle_path, bundle_output_dir)
        
        if not extraction_result:
            return {'success': False, 'error': '提取模块失败'}
        
        # 转换为TypeScript
        conversion_result = self.convert_modules_to_typescript(extraction_result)
        
        result = {
            'success': True,
            'bundle': bundle_path,
            'extracted_modules': len(extraction_result.get('modules', [])),
            'converted_classes': len(conversion_result),
            'output_dir': bundle_output_dir
        }
        
        return result

# 创建全局实例
bundleProcessor = BundleProcessor()