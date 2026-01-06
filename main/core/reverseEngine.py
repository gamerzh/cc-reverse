#!/usr/bin/env python3
"""
Cocos Creator 逆向工程核心引擎
"""

import os
import sys
import shutil
import json

# 添加项目根目录到sys.path，确保可以导入code_reverse模块
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# 导入code_reverse模块
from code_reverse import code_reverse

# 重新实现logger函数，避免依赖外部模块
def logger():
    def info(msg, **kwargs):
        print(f"[INFO] {msg}")
    
    def success(msg, **kwargs):
        print(f"[SUCCESS] {msg}")
    
    def warn(msg, **kwargs):
        print(f"[WARN] {msg}")
    
    def error(msg, **kwargs):
        print(f"[ERROR] {msg}")
    
    def debug(msg, **kwargs):
        print(f"[DEBUG] {msg}")
    
    def exception(msg, e, **kwargs):
        print(f"[EXCEPTION] {msg}: {e}")
    
    def set_level(level):
        pass
    
    def set_verbose(verbose):
        pass
    
    return {
        "info": info,
        "success": success,
        "warn": warn,
        "error": error,
        "debug": debug,
        "exception": exception,
        "set_level": set_level,
        "set_verbose": set_verbose
    }
# 修复导入问题，直接实现loadConfig函数
def loadConfig():
    """
    加载配置文件
    
    Returns:
        dict: 配置字典
    """
    return {
        "output": {
            "createMeta": True,
            "prettify": True,
            "includeComments": True
        },
        "codeGen": {
            "language": "typescript",
            "moduleType": "commonjs",
            "indentSize": 2,
            "indent": "space"
        },
        "assets": {
            "extractTextures": True,
            "extractAudio": True,
            "extractAnimations": True,
            "optimizeSprites": False
        }
    }

# 移除模块级别的bundleProcessor导入，改为在函数内部导入，避免循环导入

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
    logger()["set_level"](log_level)
    logger()["set_verbose"](verbose)
    
    logger()["info"](f"开始处理项目: {source_path}")
    logger()["info"](f"使用Cocos Creator版本提示: {version_hint}")
    
    try:
        # 检测Cocos Creator版本并设置相应的文件路径
        logger()["info"]("检测Cocos Creator版本...")
        project_info = detectProjectVersion(source_path, version_hint)
        global_cocosVersion = project_info['version']
        logger()["success"](f"成功检测到Cocos Creator版本: {global_cocosVersion}")
        
        # 检查文件是否存在
        logger()["info"]("验证项目文件路径...")
        validatePaths(project_info['resPath'], project_info['settingsPath'], project_info['projectPath'])
        logger()["success"]("项目文件路径验证通过")
        
        # 创建临时目录和输出目录
        temp_path = os.path.join(output_path, 'temp')
        ast_path = os.path.join(temp_path, 'ast')
        
        # 创建目录
        logger()["info"](f"创建工作目录: {output_path}")
        os.makedirs(temp_path, exist_ok=True)
        os.makedirs(ast_path, exist_ok=True)
        os.makedirs(output_path, exist_ok=True)
        
        # 保存全局路径信息
        global global_paths
        logger()["info"](f"设置全局路径: source={source_path}, res={project_info['resPath']}")
        
        # 保存全局路径信息
        global global_paths
        global_paths = {
            'source': source_path,
            'output': output_path,
            'res': project_info['resPath'],
            'temp': temp_path,
            'ast': ast_path
        }
        logger()["debug"](f"全局路径设置完成: {global_paths}")
        
        # 读取项目文件
        logger()["info"]("读取项目配置文件...")
        
        # 读取settings文件
        with open(project_info['settingsPath'], 'rb') as f:
            settings = f.read()
        
        # 读取project文件，尝试多种编码
        with open(project_info['projectPath'], 'rb') as f:
            project_bytes = f.read()
        
        # 尝试解码project文件，支持多种编码
        code = None
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
        for encoding in encodings:
            try:
                code = project_bytes.decode(encoding)
                logger()["debug"](f"使用编码 {encoding} 成功解码project文件")
                break
            except UnicodeDecodeError:
                continue
        
        if code is None:
            # 如果所有编码都失败，使用latin-1作为最终回退
            code = project_bytes.decode('latin-1', errors='replace')
            logger()["warn"]("无法使用utf-8/gbk/gb2312解码项目文件，使用latin-1回退")
        
        logger()["success"]("成功读取项目配置文件")
        
        # 解析设置
        logger()["info"]("解析项目设置...")
        parseSettings(settings)
        logger()["success"]("项目设置解析完成")
        
        # 导入需要在全局变量设置后使用的模块
        from resources_reverse.resourceProcessor import resourceProcessor
        from .projectGenerator import projectGenerator
        
        # code_reverse模块已在文件顶部导入，无需重复导入
        
        # 先创建项目结构
        logger()["info"]("创建项目目录结构...")
        projectGenerator._createProjectStructure(global_paths)
        logger()["success"]("项目目录结构创建完成")
        
        # 处理资源
        logger()["info"]('开始处理资源...')
        resourceProcessor.processResources(global_paths, global_settings)
        resource_stats = resourceProcessor.getResourceStats()
        logger()["success"](f'资源处理完成，共处理 {resource_stats["total"]} 个资源')
        
        # 提取脚本文件
        logger()["info"]('开始提取脚本文件...')
        extractScriptFiles(global_paths, global_settings)
        logger()["success"]('脚本文件提取完成')
        
        # 使用新的代码逆向流程
        logger()["info"]('开始代码逆向分析...')
        
        # 收集所有JavaScript文件
        js_files = []
        
        # 1. 从jsList获取脚本文件
        js_list = global_settings.get('CCSettings', {}).get('jsList', [])
        source_path = global_paths.get('source', '')
        
        for js_file in js_list:
            # 构建完整的文件路径
            possible_paths = [
                os.path.join(source_path, js_file),  # 直接在项目根目录下
                os.path.join(source_path, 'src', js_file),  # 在src目录下
                os.path.join(source_path, js_file.replace('assets/', '')),  # 移除assets前缀
                os.path.join(source_path, 'src', js_file.replace('assets/', ''))  # 在src目录下，移除assets前缀
            ]
            
            for js_file_path in possible_paths:
                if os.path.exists(js_file_path):
                    js_files.append(js_file_path)
                    break
        
        # 2. 查找所有可能的bundle文件和JavaScript文件
        import glob
        
        # 查找各种JavaScript文件
        js_patterns = [
            os.path.join(source_path, 'assets', '**', '*.js'),
            os.path.join(source_path, 'src', '**', '*.js'),
            os.path.join(source_path, '**', '*.jsbundle'),  # Webpack bundle文件
            os.path.join(source_path, '**', '*.js')
        ]
        
        for pattern in js_patterns:
            matches = glob.glob(pattern, recursive=True)
            if matches:
                js_files.extend(matches)
                logger()["debug"](f'模式 {pattern} 匹配到 {len(matches)} 个JS文件')
        
        # 去重
        js_files = list(set(js_files))
        
        # 过滤掉不需要处理的文件
        filtered_js_files = []
        for js_file in js_files:
            # 跳过node_modules和其他非项目文件
            if 'node_modules' in js_file or '.git' in js_file or '__pycache__' in js_file:
                continue
            # 跳过可能的临时文件
            if js_file.endswith('.tmp.js') or js_file.endswith('.temp.js'):
                continue
            filtered_js_files.append(js_file)
        
        js_files = filtered_js_files
        
        if js_files:
            logger()["info"](f'找到 {len(js_files)} 个JavaScript文件，开始分析...')
            
            # 创建临时目录
            temp_dir = os.path.join(global_paths['output'], 'temp')
            json_output = os.path.join(temp_dir, 'json')
            
            # 初始化代码逆向实例
            from code_reverse import CodeReverse
            reverse = CodeReverse()
            reverse.set_config('preserve_temp', verbose)
            
            # 使用JS分析器分析所有代码文件
            success = reverse.analyze_code(
                source_path,  # 传入整个源目录
                json_output,
                file_patterns=['*.js', '*.jsbundle']  # 处理所有JS和bundle文件
            )
            
            if success:
                # 检查是否生成了JSON文件
                if os.path.exists(json_output) and len(os.listdir(json_output)) > 0:
                    # 生成TypeScript代码
                    output_dir = os.path.join(global_paths['output'], 'assets', 'scripts')
                    success = reverse.generate_code(
                        json_output,
                        output_dir,
                        'typescript'
                    )
                    
                    if success:
                        # 检查生成的代码文件
                        if os.path.exists(output_dir) and len(os.listdir(output_dir)) > 0:
                            logger()["success"](f'代码逆向分析完成，生成了 {len(os.listdir(output_dir))} 个TypeScript文件')
                        else:
                            logger()["warn"]('代码生成成功，但未生成任何代码文件')
                    else:
                        logger()["error"]("代码生成失败")
                else:
                    logger()["warn"]('代码分析成功，但未生成任何JSON文件')
            else:
                logger()["error"]("代码分析失败")
        else:
            logger()["warn"]('未找到任何JavaScript文件')
        
        # 生成项目文件
        logger()["info"]('生成项目配置文件...')
        projectGenerator.generateProject(global_paths)
        logger()["success"](f'项目生成完成，共生成 {len(projectGenerator.getGeneratedFiles())} 个文件')
        
        # 清理临时文件
        if not verbose:
            logger()["info"]('清理临时文件...')
            shutil.rmtree(temp_path, ignore_errors=True)
            logger()["success"]('临时文件清理完成')
        
        logger()["success"](f'逆向工程完成！项目已生成到: {output_path}')
        return True
    except FileNotFoundError as e:
        logger()["exception"]('项目文件不存在', e)
        raise
    except PermissionError as e:
        logger()["exception"]('没有权限访问项目文件', e)
        raise
    except UnicodeDecodeError as e:
        logger()["exception"]('项目文件编码错误', e)
        raise
    except json.JSONDecodeError as e:
        logger()["exception"]('项目配置文件解析错误', e)
        raise
    except Exception as e:
        logger()["exception"]('处理项目文件时出错', e)
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
        import glob
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
        import glob
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
            logger()["info"](f'优先使用src目录下的settings文件: {settings24}')
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
                logger()["info"](f'使用assets目录作为资源目录: {res24}')
        
        # 对于2.4.15版本，project.js可能不存在，尝试使用settings.js作为project.js
        project24 = findExistingPath(paths24x['project'])
        if not project24 and settings24:
            # 如果找不到project.js，使用settings.js作为project.js
            project24 = settings24
            logger()["info"]('未找到project.js，使用settings.js作为project.js')
        
        if settings24 and res24:
            logger()["info"](f'使用Cocos Creator {versionHint if versionHint == "2.4.15" else "2.4.x"}项目结构')
            logger()["info"](f'设置文件: {settings24}')
            logger()["info"](f'项目文件: {project24}')
            logger()["info"](f'资源目录: {res24}')
            return {
                'version': '2.4.x',
                'settingsPath': settings24,
                'projectPath': project24,
                'resPath': res24
            }
        else:
            logger()["warn"](f'用户指定{versionHint if versionHint == "2.4.15" else "2.4.x"}版本，但未找到对应文件结构，尝试自动检测...')
            logger()["warn"](f'settings24: {settings24}')
            logger()["warn"](f'res24: {res24}')
    elif versionHint == '2.3.x':
        settings23 = findExistingPath(paths23x['settings'])
        project23 = findExistingPath(paths23x['project'])
        res23 = findExistingPath(paths23x['res'])
        
        if settings23 and project23 and res23:
            logger()["info"]('使用用户指定的Cocos Creator 2.3.x项目结构')
            return {
                'version': '2.3.x',
                'settingsPath': settings23,
                'projectPath': project23,
                'resPath': res23
            }
        else:
            logger()["warn"]('用户指定2.3.x版本，但未找到对应文件结构，尝试自动检测...')
    
    # 自动检测：先尝试2.3.x路径（更精确的检测）
    settings23 = findExistingPath(paths23x['settings'])
    project23 = findExistingPath(paths23x['project'])
    res23 = findExistingPath(paths23x['res'])
    
    if settings23 and project23 and res23:
        logger()["info"]('自动检测到Cocos Creator 2.3.x或更早版本项目结构')
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
            logger()["info"](f'使用assets目录作为资源目录: {res24}')
        else:
            # 检查res目录
            res_path = os.path.join(sourcePath, 'res')
            if os.path.exists(res_path):
                res24 = res_path
                logger()["info"](f'使用res目录作为资源目录: {res24}')
    
    if settings24:
        # 对于2.4.x版本，project.js可能不存在
        if not project24:
            project24 = settings24
            logger()["info"]('未找到project.js，使用settings.js作为project.js')
        
        logger()["info"]('自动检测到Cocos Creator 2.4.x项目结构')
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
        
        logger()["debug"]('开始解析设置文件...')
        logger()["debug"](f'设置文件内容: {settings_content[:200]}...')
        
        # 方法1: 提取CCSettings对象
        try:
            # 查找CCSettings赋值
            ccsettings_pattern = r'(window\._CCSettings|window\.CCSettings)\s*=\s*({[\s\S]*?})(?=;\s*}|;\s*\}|\}\s*;|$)'  
            ccsettings_match = re.search(ccsettings_pattern, settings_content, re.DOTALL)
            
            if ccsettings_match:
                settings_json_str = ccsettings_match.group(2)
                
                # 清理JSON字符串，使其能被json.loads解析
                # 1. 替换单引号为双引号
                settings_json_str = settings_json_str.replace("'", '"')
                
                # 2. 处理属性名（添加引号）
                settings_json_str = re.sub(r'([\w]+)\s*:', r'"\1":', settings_json_str)
                
                # 3. 移除末尾的逗号
                settings_json_str = re.sub(r",\s*([}\]])", r'\1', settings_json_str)
                
                # 4. 处理特殊值（undefined, null, true, false）
                settings_json_str = re.sub(r'\bundefined\b', r'null', settings_json_str)
                settings_json_str = re.sub(r'\btrue\b', r'true', settings_json_str)
                settings_json_str = re.sub(r'\bfalse\b', r'false', settings_json_str)
                
                # 5. 处理数字和字符串
                settings_json_str = re.sub(r'"([^"\\\r\n]*)"', r'"\1"', settings_json_str)
                
                # 解析JSON
                settings_data = json.loads(settings_json_str)
                global_settings = {'CCSettings': settings_data}
            else:
                # 方法2: 提取jsList
                js_list_match = re.search(r'jsList\s*:\s*\[(.*?)\]', settings_content, re.DOTALL)
                if js_list_match:
                    js_list_str = js_list_match.group(1)
                    # 分割并清理jsList项
                    js_list = [item.strip().strip("'").strip('"') for item in js_list_str.split(',') if item.strip()]
                    global_settings = {'CCSettings': {'jsList': js_list}}
                else:
                    global_settings = {'CCSettings': {}}
        except json.JSONDecodeError as e1:
            logger()["debug"](f'JSON解析失败，尝试提取jsList: {e1}')
            # 方法2: 提取jsList
            js_list_match = re.search(r'jsList\s*:\s*\[(.*?)\]', settings_content, re.DOTALL)
            if js_list_match:
                js_list_str = js_list_match.group(1)
                # 分割并清理jsList项
                js_list = [item.strip().strip("'").strip('"') for item in js_list_str.split(',') if item.strip()]
                global_settings = {'CCSettings': {'jsList': js_list}}
            else:
                global_settings = {'CCSettings': {}}
        except Exception as e2:
            logger()["debug"](f'解析失败，尝试简单提取: {e2}')
            # 方法3: 简单提取jsList
            js_list_items = re.findall(r'["\']([^"\']+)["\']', settings_content)
            if js_list_items:
                global_settings = {'CCSettings': {'jsList': js_list_items}}
            else:
                global_settings = {'CCSettings': {}}
        
        # 确保settings不为空
        if not global_settings or not global_settings.get('CCSettings'):
            global_settings = {'CCSettings': {}}
        
        if global_verbose:
            logger()["debug"](f'已加载项目设置: {list(global_settings.get("CCSettings", {}).keys())}')
            if 'jsList' in global_settings['CCSettings']:
                logger()["debug"](f'找到 {len(global_settings["CCSettings"]["jsList"])} 个脚本文件')
                for js_file in global_settings['CCSettings']['jsList']:
                    logger()["debug"](f'  - {js_file}')
    except Exception as e:
        logger()["error"](f'解析设置文件时出错: {e}')
        logger()["warn"]('使用默认设置')
        global_settings = {'CCSettings': {}}

def extractScriptFiles(paths, settings):
    """
    从 jsList 中提取脚本文件并复制到输出目录
    
    Args:
        paths (dict): 路径字典，包含source、output等路径
        settings (dict): 项目设置，包含CCSettings和jsList
    """
    js_list = settings.get('CCSettings', {}).get('jsList', [])
    if not js_list:
        logger()["warn"]('jsList为空，无法提取脚本文件')
        return
    
    logger()["info"](f'跳过直接拷贝编译后的脚本文件，共 {len(js_list)} 个脚本文件')
    logger()["info"]('脚本文件将通过代码分析逆向生成，不直接拷贝编译后的文件')
    
    # 不再直接拷贝编译后的脚本文件
    # 脚本文件将通过代码分析逆向生成
    
    logger()["success"]('脚本文件处理完成（通过代码分析逆向生成）')

def find_bundle_files(res_path):
    """
    查找资源目录中可能的Webpack bundle文件
    
    Args:
        res_path (str): 资源目录路径
    
    Returns:
        list: bundle文件路径列表
    """
    import glob
    import os
    
    bundle_files = []
    
    # 查找所有.js文件（排除index.*.js，因为它们是常规脚本）
    js_patterns = [
        os.path.join(res_path, '**', '*.js'),
        os.path.join(res_path, '**', '*', '*.js'),
    ]
    
    for pattern in js_patterns:
        matches = glob.glob(pattern, recursive=True)
        for match in matches:
            # 排除script目录中的.js文件（这些可能是已提取的模块）
            if 'script' in match.lower() and os.path.dirname(match).lower().endswith('script'):
                continue
            bundle_files.append(match)
    
    # 去重
    bundle_files = list(set(bundle_files))
    
    # 按文件大小排序（大的文件可能是bundle）
    bundle_files.sort(key=lambda x: os.path.getsize(x) if os.path.exists(x) else 0, reverse=True)
    
    return bundle_files

def process_bundle_files(bundle_files, output_base_dir, res_path):
    """
    处理bundle文件列表
    
    Args:
        bundle_files (list): bundle文件路径列表
        output_base_dir (str): 输出基础目录
        res_path (str): 资源目录路径，用于计算相对路径
    
    Returns:
        list: 处理结果列表
    """
    # 导入bundleProcessor，避免循环导入
    from .bundleProcessor import bundleProcessor
    
    results = []
    
    for bundle_file in bundle_files:
        try:
            # 检查是否为Webpack bundle
            if bundleProcessor.is_webpack_bundle(bundle_file):
                logger()["info"](f"处理Webpack bundle: {bundle_file}")
                
                # 处理bundle文件
                result = bundleProcessor.process_bundle_file(bundle_file, output_base_dir, res_path)
                result['file'] = bundle_file
                results.append(result)
                
                if result.get('success'):
                    logger()["success"](f"成功处理bundle: {os.path.basename(bundle_file)} (提取 {result.get('extracted_modules', 0)} 个模块, 转换 {result.get('converted_classes', 0)} 个类)")
                else:
                    logger()["error"](f"处理bundle失败: {os.path.basename(bundle_file)}: {result.get('error', '未知错误')}")
            else:
                logger()["debug"](f"跳过非Webpack bundle文件: {bundle_file}")
        except Exception as e:
            logger()["error"](f"处理bundle文件时出错 {bundle_file}: {e}")
            results.append({
                'file': bundle_file,
                'success': False,
                'error': str(e)
            })
    
    return results
