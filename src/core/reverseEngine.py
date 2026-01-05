#!/usr/bin/env python3
"""
Cocos Creator 逆向工程核心引擎
"""

import os
import sys
import shutil
import json
from utils.fileManager import fileManager
from utils.logger import logger
from config.configLoader import loadConfig

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
    silent = options.get('silent', False)
    version_hint = options.get('versionHint', '')
    
    # 全局配置初始化
    global global_config, global_verbose, global_cocosVersion, global_settings, global_paths
    global_config = loadConfig()
    global_verbose = verbose
    
    # 配置日志
    log_level = "debug" if verbose else "info"
    if silent:
        log_level = "error"
    logger().set_level(log_level)
    logger().set_verbose(verbose)
    
    logger().info(f"开始处理项目: {source_path}", output=output_path)
    logger().info(f"使用Cocos Creator版本提示: {version_hint}")
    
    try:
        # 检测Cocos Creator版本并设置相应的文件路径
        logger().info("检测Cocos Creator版本...")
        project_info = detectProjectVersion(source_path, version_hint)
        global_cocosVersion = project_info['version']
        logger().success(f"成功检测到Cocos Creator版本: {global_cocosVersion}")
        
        # 检查文件是否存在
        logger().info("验证项目文件路径...")
        validatePaths(project_info['resPath'], project_info['settingsPath'], project_info['projectPath'])
        logger().success("项目文件路径验证通过")
        
        # 创建临时目录和输出目录
        temp_path = os.path.join(output_path, 'temp')
        ast_path = os.path.join(temp_path, 'ast')
        
        # 创建目录
        logger().info(f"创建工作目录: {output_path}")
        os.makedirs(temp_path, exist_ok=True)
        os.makedirs(ast_path, exist_ok=True)
        os.makedirs(output_path, exist_ok=True)
        
        # 保存全局路径信息
        global global_paths
        logger().info(f"设置全局路径: source={source_path}, res={project_info['resPath']}")
        global_paths = {
            'source': source_path,
            'output': output_path,
            'res': project_info['resPath'],
            'temp': temp_path,
            'ast': ast_path
        }
        logger().debug(f"全局路径设置完成: {global_paths}")
        
        # 读取项目文件
        logger().info("读取项目配置文件...")
        with open(project_info['settingsPath'], 'rb') as f:
            settings = f.read()
        
        with open(project_info['projectPath'], 'rb') as f:
            project = f.read()
        
        code = project.decode('utf-8')
        logger().success("成功读取项目配置文件")
        
        # 解析设置
        logger().info("解析项目设置...")
        parseSettings(settings)
        logger().success("项目设置解析完成")
        
        # 导入需要在全局变量设置后使用的模块
        from core.codeAnalyzer import codeAnalyzer
        from core.resourceProcessor import resourceProcessor
        from core.projectGenerator import projectGenerator
        
        # 先创建项目结构
        logger().info("创建项目目录结构...")
        projectGenerator._createProjectStructure(global_paths)
        logger().success("项目目录结构创建完成")
        
        # 分析主项目文件
        logger().info('开始分析主项目文件...')
        codeAnalyzer.analyze(code)
        components_count = len(codeAnalyzer.analyzed_data.get('components', []))
        logger().success(f"主项目文件分析完成，检测到 {components_count} 个组件")
        
        if components_count > 0:
            logger().info(f"检测到的组件: {[c.get('name') for c in codeAnalyzer.analyzed_data.get('components', [])]}")
        
        # 分析settings中列出的所有JavaScript文件
        js_list = global_settings.get('CCSettings', {}).get('jsList', [])
        if js_list:
            logger().info(f'开始分析 {len(js_list)} 个额外脚本文件...')
            source_path = global_paths.get('source', '')
            js_files = []
            missing_files = []
            
            for js_file in js_list:
                # 构建完整的文件路径
                # 尝试多种可能的路径
                possible_paths = [
                    os.path.join(source_path, js_file),  # 直接在项目根目录下
                    os.path.join(source_path, 'src', js_file),  # 在src目录下
                    os.path.join(source_path, js_file.replace('assets/', '')),  # 移除assets前缀
                    os.path.join(source_path, 'src', js_file.replace('assets/', ''))  # 在src目录下，移除assets前缀
                ]
                
                found = False
                for js_file_path in possible_paths:
                    if os.path.exists(js_file_path):
                        js_files.append(js_file_path)
                        found = True
                        break
                
                if not found:
                    missing_files.append(js_file)
        
        # 报告缺失的文件
        if missing_files:
            logger().warn(f'未找到 {len(missing_files)} 个脚本文件: {missing_files[:5]}{"..." if len(missing_files) > 5 else ""}')
        
        # 分析所有找到的脚本文件
        if js_files:
            logger().info(f'分析找到的 {len(js_files)} 个脚本文件...')
            codeAnalyzer.analyzeMultipleFiles(js_files)
            logger().success(f'额外脚本文件分析完成，累计检测到 {len(codeAnalyzer.analyzed_data.get("components", []))} 个组件')
        
        # 查找并分析所有index.*.js文件（包含编译后的游戏逻辑）
        logger().info('开始查找并分析index.*.js文件...')
        import glob
        source_path = global_paths.get('source', '')
        index_files = []
        # 查找assets目录下的所有index.*.js文件
        index_patterns = [
            os.path.join(source_path, 'assets', '*', 'index.*.js'),
            os.path.join(source_path, 'assets', '*', '*', 'index.*.js'),
            os.path.join(source_path, 'assets', '*', '*', '*', 'index.*.js'),
        ]
        for pattern in index_patterns:
            matches = glob.glob(pattern)
            if matches:
                index_files.extend(matches)
                logger().debug(f'模式 {pattern} 匹配到 {len(matches)} 个文件')
        
        # 去重
        index_files = list(set(index_files))
        logger().info(f'找到 {len(index_files)} 个index.*.js文件')
        
        # 分析这些文件
        if index_files:
            logger().info(f'开始分析index.*.js文件...')
            codeAnalyzer.analyzeMultipleFiles(index_files)
            logger().success(f'index.*.js文件分析完成，累计检测到 {len(codeAnalyzer.analyzed_data.get("components", []))} 个组件')
        else:
            logger().warn('未找到任何index.*.js文件')
        
        # 处理资源
        logger().info('开始处理资源...')
        resourceProcessor.processResources(global_paths)
        resource_stats = resourceProcessor.getResourceStats()
        logger().success(f'资源处理完成，共处理 {resource_stats["total"]} 个资源')
        
        # 提取脚本文件
        logger().info('开始提取脚本文件...')
        extractScriptFiles(global_paths, global_settings)
        logger().success('脚本文件提取完成')
        
        # 生成脚本文件（如果需要从编译后的代码中提取组件）
        if codeAnalyzer.analyzed_data.get('components', []):
            components_count = len(codeAnalyzer.analyzed_data.get('components', []))
            logger().info(f'检测到 {components_count} 个组件，开始生成脚本文件...')
            codeAnalyzer.generateScripts(global_paths.get('output', ''))
            logger().success(f'脚本文件生成完成，共生成 {components_count} 个脚本文件')
        else:
            logger().warn('未检测到任何组件')
        
        # 生成项目文件
        logger().info('生成项目配置文件...')
        projectGenerator.generateProject(global_paths)
        logger().success(f'项目生成完成，共生成 {len(projectGenerator.getGeneratedFiles())} 个文件')
        
        # 清理临时文件
        if not verbose:
            logger().info('清理临时文件...')
            fileManager.cleanDirectory(temp_path)
            logger().success('临时文件清理完成')
        
        logger().success(f'逆向工程完成！项目已生成到: {output_path}')
        return True
    except FileNotFoundError as e:
        logger().exception('项目文件不存在', e)
        raise
    except PermissionError as e:
        logger().exception('没有权限访问项目文件', e)
        raise
    except UnicodeDecodeError as e:
        logger().exception('项目文件编码错误', e)
        raise
    except json.JSONDecodeError as e:
        logger().exception('项目配置文件解析错误', e)
        raise
    except Exception as e:
        logger().exception('处理项目文件时出错', e)
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
            os.path.join(sourcePath, 'src', 'settings*.js'),  # 优先查找src目录下的settings文件
            os.path.join(sourcePath, 'main*.js'),
            os.path.join(sourcePath, 'settings*.js')
        ],
        'project': [
            os.path.join(sourcePath, 'main*.js'),  # 主文件可能包含项目配置
            os.path.join(sourcePath, 'src', 'project*.js'),
            os.path.join(sourcePath, 'project*.js')
        ],
        'res': [
            os.path.join(sourcePath, 'assets'),  # 编译后的资源目录
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
            # 先尝试直接检查路径是否存在
            if os.path.exists(pattern):
                return pattern
            # 使用glob查找匹配的文件
            matches = glob.glob(pattern)
            if matches:
                # 返回第一个匹配的文件
                return matches[0]
        return None
    
    def findAllMatchingFiles(pathArray):
        """查找所有匹配的文件，支持通配符模式"""
        all_matches = []
        for pattern in pathArray:
            # 使用glob查找匹配的文件
            matches = glob.glob(pattern)
            if matches:
                all_matches.extend(matches)
        return all_matches
    
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
    
    # 特殊处理资源目录，确保能找到编译后的资源
    res24 = findExistingPath(paths24x['res'])
    
    # 如果没找到，直接检查assets目录
    if not res24:
        assets_path = os.path.join(sourcePath, 'assets')
        if os.path.exists(assets_path):
            res24 = assets_path
            logger().info(f'使用assets目录作为资源目录: {res24}')
        else:
            # 检查res目录
            res_path = os.path.join(sourcePath, 'res')
            if os.path.exists(res_path):
                res24 = res_path
                logger().info(f'使用res目录作为资源目录: {res24}')
    
    if settings24:
        # 对于2.4.x版本，project.js可能不存在
        if not project24:
            project24 = settings24
            logger().info('未找到project.js，使用settings.js作为project.js')
        
        logger().info('自动检测到Cocos Creator 2.4.x项目结构')
        return {
            'version': '2.4.x',
            'settingsPath': settings24,
            'projectPath': project24,
            'resPath': res24 or sourcePath
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
                # 查找window._CCSettings的完整赋值
                ccsettings_match = re.search(r'window\._CCSettings\s*=\s*({[^;]+});', settings_content, re.DOTALL)
                if ccsettings_match:
                    settings_json_str = ccsettings_match.group(1)
                else:
                    # 如果没有分号，尝试匹配到行尾
                    ccsettings_match = re.search(r'window\._CCSettings\s*=\s*({[^;]+})', settings_content, re.DOTALL)
                    if ccsettings_match:
                        settings_json_str = ccsettings_match.group(1)
                    else:
                        # 保留原逻辑作为备选
                        settings_line = settings_content.strip()
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
                # 提取整个赋值语句
                # 查找window.CCSettings的完整赋值
                ccsettings_match = re.search(r'window\.CCSettings\s*=\s*({[^;]+});', settings_content, re.DOTALL)
                if ccsettings_match:
                    settings_json_str = ccsettings_match.group(1)
                else:
                    # 如果没有分号，尝试匹配到行尾
                    ccsettings_match = re.search(r'window\.CCSettings\s*=\s*({[^;]+})', settings_content, re.DOTALL)
                    if ccsettings_match:
                        settings_json_str = ccsettings_match.group(1)
                    else:
                        # 保留原逻辑作为备选
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

def extractScriptFiles(paths, settings):
    """
    从 jsList 中提取脚本文件并复制到输出目录
    
    Args:
        paths (dict): 路径字典，包含source、output等路径
        settings (dict): 项目设置，包含CCSettings和jsList
    """
    from utils.logger import logger
    from utils.fileManager import fileManager
    import shutil
    
    js_list = settings.get('CCSettings', {}).get('jsList', [])
    if not js_list:
        logger().warn('jsList为空，无法提取脚本文件')
        return
    
    source_path = paths.get('source', '')
    output_path = paths.get('output', '')
    
    if not source_path or not output_path:
        logger().error('缺少必要的路径信息')
        return
    
    logger().info(f'开始从jsList中提取 {len(js_list)} 个脚本文件...')
    
    copied_count = 0
    missing_count = 0
    
    for js_file_path in js_list:
        # 移除assets/前缀（如果存在）
        if js_file_path.startswith('assets/'):
            rel_path = js_file_path[7:]  # 移除 'assets/' 前缀
        else:
            rel_path = js_file_path
        
        # 构建源文件路径（尝试多种可能的位置）
        possible_source_paths = [
            os.path.join(source_path, js_file_path),  # 完整路径
            os.path.join(source_path, rel_path),  # 移除assets前缀后的路径
            os.path.join(source_path, 'src', js_file_path),  # 在src目录下
            os.path.join(source_path, 'src', rel_path),  # 在src目录下，移除assets前缀
            os.path.join(source_path, 'assets', rel_path),  # 在assets目录下
        ]
        
        source_file = None
        for possible_path in possible_source_paths:
            if os.path.exists(possible_path) and os.path.isfile(possible_path):
                source_file = possible_path
                break
        
        if not source_file:
            logger().debug(f'未找到脚本文件: {js_file_path}')
            missing_count += 1
            continue
        
        # 构建输出路径：保持原始路径结构
        # 如果js_file_path是 'assets/scripts/module/script.ts'
        # 输出路径应该是 'output/assets/scripts/module/script.ts'
        # 如果js_file_path是 'scripts/module/script.ts'
        # 输出路径应该是 'output/assets/scripts/module/script.ts'
        # 注意：output_path 已经是输出目录，projectGenerator 会在其下创建 assets 目录
        # 所以如果 js_file_path 包含 'assets/'，需要移除它以避免嵌套
        
        if js_file_path.startswith('assets/'):
            # 移除 assets/ 前缀，因为输出目录下已经有 assets 目录了
            path_without_assets = js_file_path[7:]  # 移除 'assets/' 前缀
            output_file_path = os.path.join(output_path, 'assets', path_without_assets)
        elif js_file_path.startswith('scripts/'):
            # 如果以scripts/开头，添加到assets/下
            output_file_path = os.path.join(output_path, 'assets', js_file_path)
        else:
            # 如果路径不以assets/或scripts/开头，假设它在assets/scripts下
            output_file_path = os.path.join(output_path, 'assets', 'scripts', rel_path)
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file_path)
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # 复制文件
            shutil.copy2(source_file, output_file_path)
            logger().debug(f'复制脚本文件: {js_file_path} -> {output_file_path}')
            copied_count += 1
        except Exception as e:
            logger().error(f'复制脚本文件失败 {js_file_path}: {e}')
            missing_count += 1
    
    logger().info(f'脚本文件提取完成: 成功 {copied_count} 个, 缺失 {missing_count} 个')
    
    # 如果从编译后的代码中提取的组件，也生成脚本文件
    # 这部分逻辑在reverseProject中处理
