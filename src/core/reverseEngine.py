#!/usr/bin/env python3
"""
Cocos Creator 逆向工程核心引擎
"""

import os
import sys
import shutil
from src.utils.fileManager import fileManager
from src.utils.logger import logger
from src.config.configLoader import loadConfig

global_config = {}
global_verbose = False
global_cocosVersion = ""
global_settings = {}
global_paths = {}

def reverseProject(options):
    """
    逆向工程主函数
    
    Args:
        options (dict): 配置选项
            sourcePath (str): 源项目路径
            outputPath (str): 输出路径
            verbose (bool): 是否显示详细日志
            silent (bool): 是否静默模式
            versionHint (str): 版本提示
    
    Returns:
        bool: 成功返回True，失败返回False
    """
    source_path = options.get('sourcePath')
    output_path = options.get('outputPath')
    verbose = options.get('verbose', False)
    version_hint = options.get('versionHint', '')
    
    # 全局配置初始化
    global global_config, global_verbose, global_cocosVersion, global_settings, global_paths
    global_config = loadConfig()
    global_verbose = verbose
    
    # 检测Cocos Creator版本并设置相应的文件路径
    project_info = detectProjectVersion(source_path, version_hint)
    global_cocosVersion = project_info['version']
    
    # 检查文件是否存在
    validatePaths(project_info['resPath'], project_info['settingsPath'], project_info['projectPath'])
    
    # 创建临时目录和输出目录
    temp_path = os.path.join(output_path, 'temp')
    ast_path = os.path.join(temp_path, 'ast')
    
    # 创建目录
    os.makedirs(temp_path, exist_ok=True)
    os.makedirs(ast_path, exist_ok=True)
    os.makedirs(output_path, exist_ok=True)
    
    # 保存全局路径信息
    global_paths = {
        'source': source_path,
        'output': output_path,
        'res': project_info['resPath'],
        'temp': temp_path,
        'ast': ast_path
    }
    
    try:
        # 读取项目文件
        with open(project_info['settingsPath'], 'rb') as f:
            settings = f.read()
        
        with open(project_info['projectPath'], 'rb') as f:
            project = f.read()
        
        code = project.decode('utf-8')
        
        # 解析设置
        parseSettings(settings)
        
        # 开始处理
        logger().info('开始分析代码...')
        
        # 导入需要在全局变量设置后使用的模块
        from src.core.codeAnalyzer import codeAnalyzer
        from src.core.resourceProcessor import resourceProcessor
        from src.core.projectGenerator import projectGenerator
        
        # 分析主项目文件
        codeAnalyzer.analyze(code)
        
        # 分析settings中列出的所有JavaScript文件
        js_list = global_settings.get('CCSettings', {}).get('jsList', [])
        if js_list:
            logger().info(f'开始分析 {len(js_list)} 个额外脚本文件...')
            source_path = global_paths.get('source', '')
            js_files = []
            
            for js_file in js_list:
                # 构建完整的文件路径
                js_file_path = os.path.join(source_path, js_file)
                if os.path.exists(js_file_path):
                    js_files.append(js_file_path)
                else:
                    # 尝试在src目录下查找
                    js_file_path_src = os.path.join(source_path, 'src', js_file)
                    if os.path.exists(js_file_path_src):
                        js_files.append(js_file_path_src)
                    else:
                        logger().warn(f'未找到脚本文件: {js_file}')
            
            # 分析所有找到的脚本文件
            if js_files:
                codeAnalyzer.analyzeMultipleFiles(js_files)
        
        logger().info('开始处理资源...')
        # 处理资源
        resourceProcessor.processResources()
        
        # 生成脚本文件
        if codeAnalyzer.analyzed_data.get('components', []):
            logger().info('生成脚本文件...')
            codeAnalyzer.generateScripts(global_paths.get('output', ''))
        
        logger().info('生成项目文件...')
        # 生成项目，传入全局路径
        projectGenerator.generateProject(global_paths)
        
        # 清理临时文件
        if not verbose:
            fileManager.cleanDirectory(temp_path)
        
        return True
    except Exception as e:
        logger().error(f'处理项目文件时出错: {e}')
        raise

def detectProjectVersion(sourcePath, versionHint):
    """
    检测Cocos Creator项目版本并返回相应的文件路径
    
    Args:
        sourcePath (str): 源项目路径
        versionHint (str): 版本提示
    
    Returns:
        dict: 包含版本信息和文件路径的对象
    """
    import glob
    
    # 2.4.x版本的可能路径（支持带md5值的文件名）
    paths24x = {
        'settings': [
            os.path.join(sourcePath, 'main*.js'),
            os.path.join(sourcePath, 'settings*.js'),
            os.path.join(sourcePath, 'src', 'settings*.js')
        ],
        'project': [
            os.path.join(sourcePath, 'project*.js'),
            os.path.join(sourcePath, 'main*.js'),
            os.path.join(sourcePath, 'src', 'project*.js')
        ],
        'res': [
            os.path.join(sourcePath, 'assets'),
            os.path.join(sourcePath, 'res'),
            os.path.join(sourcePath, 'src', 'assets')
        ]
    }
    
    # 2.3.x及以下版本的路径
    paths23x = {
        'settings': [os.path.join(sourcePath, 'src', 'settings*.js')],
        'project': [os.path.join(sourcePath, 'src', 'project*.js')],
        'res': [os.path.join(sourcePath, 'res')]
    }
    
    def findExistingPath(pathArray):
        """查找存在的路径，支持通配符模式"""
        for pattern in pathArray:
            # 使用glob查找匹配的文件
            matches = glob.glob(pattern)
            if matches:
                # 返回第一个匹配的文件
                return matches[0]
        return None
    
    # 特殊处理2.4.15版本提示
    if versionHint == '2.4.15' or versionHint == '2.4.x':
        # 先尝试查找src/settings*.js作为优先设置文件
        src_settings_pattern = os.path.join(sourcePath, 'src', 'settings*.js')
        src_settings = glob.glob(src_settings_pattern)
        
        if src_settings:
            # 如果找到src/settings*.js，优先使用它
            settings24 = src_settings[0]
            logger().info(f'优先使用src目录下的settings文件: {settings24}')
        else:
            # 否则使用默认查找
            settings24 = findExistingPath(paths24x['settings'])
        
        # 查找资源目录
        res24 = findExistingPath(paths24x['res'])
        if not res24:
            # 尝试直接在sourcePath下查找assets目录
            assets_path = os.path.join(sourcePath, 'assets')
            if os.path.exists(assets_path):
                res24 = assets_path
                logger().info(f'使用assets目录作为资源目录: {res24}')
        
        # 对于2.4.15版本，project.js可能不存在，尝试使用settings.js作为project.js
        project24 = findExistingPath(paths24x['project'])
        if not project24 and settings24:
            # 如果找不到project.js，使用settings.js作为project.js
            project24 = settings24
            logger().info('未找到project.js，使用settings.js作为project.js')
        
        if settings24 and res24:
            logger().info(f'使用Cocos Creator {versionHint if versionHint == "2.4.15" else "2.4.x"}项目结构')
            logger().info(f'设置文件: {settings24}')
            logger().info(f'项目文件: {project24}')
            logger().info(f'资源目录: {res24}')
            return {
                'version': '2.4.x',
                'settingsPath': settings24,
                'projectPath': project24,
                'resPath': res24
            }
        else:
            logger().warn(f'用户指定{versionHint if versionHint == "2.4.15" else "2.4.x"}版本，但未找到对应文件结构，尝试自动检测...')
            logger().warn(f'settings24: {settings24}')
            logger().warn(f'res24: {res24}')
    elif versionHint == '2.3.x':
        settings23 = findExistingPath(paths23x['settings'])
        project23 = findExistingPath(paths23x['project'])
        res23 = findExistingPath(paths23x['res'])
        
        if settings23 and project23 and res23:
            logger().info('使用用户指定的Cocos Creator 2.3.x项目结构')
            return {
                'version': '2.3.x',
                'settingsPath': settings23,
                'projectPath': project23,
                'resPath': res23
            }
        else:
            logger().warn('用户指定2.3.x版本，但未找到对应文件结构，尝试自动检测...')
    
    # 自动检测：先尝试2.3.x路径（更精确的检测）
    settings23 = findExistingPath(paths23x['settings'])
    project23 = findExistingPath(paths23x['project'])
    res23 = findExistingPath(paths23x['res'])
    
    if settings23 and project23 and res23:
        logger().info('自动检测到Cocos Creator 2.3.x或更早版本项目结构')
        return {
            'version': '2.3.x',
            'settingsPath': settings23,
            'projectPath': project23,
            'resPath': res23
        }
    
    # 再尝试2.4.x路径
    settings24 = findExistingPath(paths24x['settings'])
    project24 = findExistingPath(paths24x['project'])
    res24 = findExistingPath(paths24x['res'])
    
    if settings24 and res24:
        # 对于2.4.x版本，project.js可能不存在
        if not project24:
            project24 = settings24
            logger().info('未找到project.js，使用settings.js作为project.js')
        
        logger().info('自动检测到Cocos Creator 2.4.x项目结构')
        return {
            'version': '2.4.x',
            'settingsPath': settings24,
            'projectPath': project24,
            'resPath': res24
        }
    
    # 如果都找不到，抛出详细错误信息
    raise Exception(
        f'无法检测到有效的Cocos Creator项目结构，请检查输入路径是否正确。\n'\
        f'支持的文件结构：\n'\
        f'2.4.x: main*.js/settings*.js + project*.js/main*.js + assets/res目录\n'\
        f'2.3.x: src/settings*.js + src/project*.js + res目录'
    )

def validatePaths(resPath, settingsPath, projectPath):
    """
    验证路径是否存在
    
    Args:
        resPath (str): 资源路径
        settingsPath (str): 设置文件路径
        projectPath (str): 项目文件路径
    """
    if not os.path.exists(resPath):
        raise Exception(f'错误: 资源路径不存在: {resPath}')
    
    if not os.path.exists(settingsPath):
        raise Exception(f'错误: 设置文件不存在: {settingsPath}')
    
    # 对于2.4.15版本，projectPath可能与settingsPath相同，所以只需要验证一次
    if projectPath != settingsPath and not os.path.exists(projectPath):
        # 尝试查找其他可能的project文件
        import glob
        project_dir = os.path.dirname(projectPath)
        project_files = glob.glob(os.path.join(project_dir, 'project*.js'))
        if project_files:
            # 如果找到其他project文件，使用第一个
            raise Exception(f'错误: 指定的project.js文件不存在，但找到其他project文件: {project_files[0]}')
        else:
            raise Exception(f'错误: project.js 文件不存在: {projectPath}')

def parseSettings(settings):
    """
    解析设置文件
    
    Args:
        settings (bytes): 设置文件内容
    """
    global global_cocosVersion, global_settings
    
    try:
        settings_content = settings.decode('utf-8')
        
        # 解析window._CCSettings或window.CCSettings
        import re
        import json
        
        logger().debug('开始解析设置文件...')
        logger().debug(f'设置文件内容: {settings_content[:200]}...')
        
        # 方法1: 直接执行JavaScript代码获取CCSettings（安全方式）
        try:
            # 使用ast.literal_eval或直接解析
            # 查找CCSettings赋值行
            if 'window._CCSettings' in settings_content:
                # 提取整个赋值语句
                settings_line = settings_content.strip()
                # 移除window._CCSettings = 和最后的分号
                settings_json_str = settings_line.replace('window._CCSettings=', '').rstrip(';')
                
                # 使用一个简单的JavaScript解析器来处理
                # 替换单引号为双引号
                settings_json_str = settings_json_str.replace("'", '"')
                # 移除末尾的逗号
                settings_json_str = re.sub(r",\s*([}\]])", r'\1', settings_json_str)
                
                # 解析JSON
                settings_data = json.loads(settings_json_str)
                global_settings = {'CCSettings': settings_data}
            elif 'window.CCSettings' in settings_content:
                settings_line = settings_content.strip()
                settings_json_str = settings_line.replace('window.CCSettings=', '').rstrip(';')
                settings_json_str = settings_json_str.replace("'", '"')
                settings_json_str = re.sub(r",\s*([}\]])", r'\1', settings_json_str)
                settings_data = json.loads(settings_json_str)
                global_settings = {'CCSettings': settings_data}
            else:
                # 尝试方法2: 提取jsList
                js_list_match = re.search(r'jsList\s*:\s*\[(.*?)\]', settings_content, re.DOTALL)
                if js_list_match:
                    js_list_str = js_list_match.group(1)
                    # 分割并清理jsList项
                    js_list = [item.strip().strip("'").strip('"') for item in js_list_str.split(',')]
                    global_settings = {'CCSettings': {'jsList': js_list}}
                else:
                    global_settings = {'CCSettings': {}}
        except Exception as e1:
            logger().debug(f'直接解析失败，尝试提取jsList: {e1}')
            # 方法2: 提取jsList
            js_list_match = re.search(r'jsList\s*:\s*\[(.*?)\]', settings_content, re.DOTALL)
            if js_list_match:
                js_list_str = js_list_match.group(1)
                # 分割并清理jsList项
                js_list = [item.strip().strip("'").strip('"') for item in js_list_str.split(',')]
                global_settings = {'CCSettings': {'jsList': js_list}}
            else:
                global_settings = {'CCSettings': {}}
        
        # 确保settings不为空
        if not global_settings or not global_settings.get('CCSettings'):
            global_settings = {'CCSettings': {}}
        
        if global_verbose:
            logger().debug(f'已加载项目设置: {list(global_settings.get("CCSettings", {}).keys())}')
            if 'jsList' in global_settings['CCSettings']:
                logger().debug(f'找到 {len(global_settings["CCSettings"]["jsList"])} 个脚本文件')
                for js_file in global_settings['CCSettings']['jsList']:
                    logger().debug(f'  - {js_file}')
    except Exception as e:
        logger().error(f'解析设置文件时出错: {e}')
        logger().warn('使用默认设置')
        global_settings = {'CCSettings': {}}
