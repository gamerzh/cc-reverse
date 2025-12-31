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
        
        # 分析代码
        codeAnalyzer.analyze(code)
        
        logger().info('开始处理资源...')
        # 处理资源
        resourceProcessor.processResources()
        
        logger().info('生成项目文件...')
        # 生成项目
        projectGenerator.generateProject()
        
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
    # 2.4.x版本的可能路径
    paths24x = {
        'settings': [
            os.path.join(sourcePath, 'main.js'),
            os.path.join(sourcePath, 'settings.js'),
            os.path.join(sourcePath, 'src', 'settings.js')
        ],
        'project': [
            os.path.join(sourcePath, 'project.js'),
            os.path.join(sourcePath, 'main.js'),
            os.path.join(sourcePath, 'src', 'project.js')
        ],
        'res': [
            os.path.join(sourcePath, 'assets'),
            os.path.join(sourcePath, 'res'),
            os.path.join(sourcePath, 'src', 'assets')
        ]
    }
    
    # 2.3.x及以下版本的路径
    paths23x = {
        'settings': [os.path.join(sourcePath, 'src', 'settings.js')],
        'project': [os.path.join(sourcePath, 'src', 'project.js')],
        'res': [os.path.join(sourcePath, 'res')]
    }
    
    def findExistingPath(pathArray):
        """查找存在的路径"""
        for filePath in pathArray:
            if os.path.exists(filePath):
                return filePath
        return None
    
    # 如果用户提供了版本提示，优先使用对应版本的路径
    if versionHint == '2.4.x':
        settings24 = findExistingPath(paths24x['settings'])
        project24 = findExistingPath(paths24x['project'])
        res24 = findExistingPath(paths24x['res'])
        
        if settings24 and project24 and res24:
            logger().info('使用用户指定的Cocos Creator 2.4.x项目结构')
            return {
                'version': '2.4.x',
                'settingsPath': settings24,
                'projectPath': project24,
                'resPath': res24
            }
        else:
            logger().warn('用户指定2.4.x版本，但未找到对应文件结构，尝试自动检测...')
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
    
    if settings24 and project24 and res24:
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
        f'2.4.x: main.js/settings.js + project.js/main.js + assets/res目录\n'\
        f'2.3.x: src/settings.js + src/project.js + res目录'
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
        raise Exception(f'错误: settings.js 文件不存在: {settingsPath}')
    
    if not os.path.exists(projectPath):
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
        
        # 由于Python的安全性，我们不能直接使用eval，需要使用更安全的方式解析
        # 这里我们简单模拟JS对象的解析
        
        # 根据版本使用不同的解析方式
        if global_cocosVersion == '2.4.x':
            # 2.4.x版本的解析逻辑
            if 'window.CCSettings' in settings_content:
                # 简化处理，实际项目中需要更复杂的解析
                global_settings = {'CCSettings': {}}
            else:
                # 尝试直接解析为对象
                global_settings = {'CCSettings': {}}
        else:
            # 2.3.x及以下版本的原有解析逻辑
            global_settings = {'CCSettings': {}}
        
        # 确保settings不为空
        if not global_settings or not global_settings.get('CCSettings'):
            global_settings = {'CCSettings': {}}
        
        if global_verbose:
            logger().debug(f'已加载项目设置: {list(global_settings.get("CCSettings", {}).keys())}')
    except Exception as e:
        logger().error(f'解析设置文件时出错: {e}')
        logger().warn('使用默认设置')
        global_settings = {'CCSettings': {}}
