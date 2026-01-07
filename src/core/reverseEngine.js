/*
 * @Date: 2025-06-07 10:06:12
 * @Description: Cocos Creator 逆向工程核心引擎
 */
const fs = require('fs');
const path = require('path');
const { promisify } = require('util');
const { fileManager } = require('../utils/fileManager');
const { codeAnalyzer } = require('./codeAnalyzer');
const { resourceProcessor } = require('./resourceProcessor');
const { projectGenerator } = require('./projectGenerator');
const { logger } = require('../utils/logger');
const { loadConfig } = require('../config/configLoader');

// 将异步文件操作转为 Promise
const readFile = promisify(fs.readFile);
const mkdir = promisify(fs.mkdir);

/**
 * 逆向工程主函数
 * @param {Object} options 配置选项
 * @param {string} options.sourcePath 源项目路径
 * @param {string} options.outputPath 输出路径
 * @param {boolean} options.verbose 是否显示详细日志
 * @param {boolean} options.silent 是否静默模式
 * @param {string} options.versionHint 版本提示
 * @returns {Promise<void>}
 */
async function reverseProject(options) {
  const { sourcePath, outputPath, verbose = false, versionHint } = options;
  
  // 全局配置初始化
  global.config = loadConfig();
  global.verbose = verbose;
  
  logger.info('========================================');
  logger.info('开始执行 Cocos Creator 逆向工程');
  logger.info('========================================');
  logger.info(`源项目路径: ${sourcePath}`);
  logger.info(`输出路径: ${outputPath}`);
  logger.info(`详细模式: ${verbose}`);
  logger.info(`版本提示: ${versionHint || '自动检测'}`);
  logger.info('========================================');
  
  // 检测Cocos Creator版本并设置相应的文件路径
  const projectInfo = detectProjectVersion(sourcePath, versionHint);
  global.cocosVersion = projectInfo.version;
  
  // 打印找到的路径信息
  logger.info(`找到的项目信息:`);
  logger.info(`- 版本: ${projectInfo.version}`);
  logger.info(`- 资源路径: ${projectInfo.resPath}`);
  logger.info(`- 设置文件路径: ${projectInfo.settingsPath}`);
  logger.info(`- 项目文件路径: ${projectInfo.projectPath}`);
  
  // 检查文件是否存在
  validatePaths(projectInfo.resPath, projectInfo.settingsPath, projectInfo.projectPath);
  
  // 创建临时目录和输出目录
  const tempPath = path.resolve(outputPath, 'temp');
  const astPath = path.resolve(tempPath, 'ast');
  logger.info(`创建临时目录: ${tempPath}`);
  await mkdir(tempPath, { recursive: true });
  logger.info(`创建 AST 目录: ${astPath}`);
  await mkdir(astPath, { recursive: true });
  logger.info(`创建输出目录: ${outputPath}`);
  await mkdir(outputPath, { recursive: true });
  logger.info('所有目录创建完成');
  
  // 保存全局路径信息
  global.paths = {
    source: sourcePath,
    output: outputPath,
    res: projectInfo.resPath,
    temp: tempPath,
    ast: astPath
  };
  
  // 读取项目文件
  try {
    logger.info('读取项目文件...');
    // 读取和解析设置
    const settings = await readFile(projectInfo.settingsPath);
    const project = await readFile(projectInfo.projectPath);
    const code = project.toString('utf-8');
    
    logger.info('解析设置文件...');
    // 解析设置
    parseSettings(settings);
    
    // 打印调试信息
    logger.info('设置解析后:');
    logger.info('global.settings 是否为空:', !global.settings);
    if (global.settings) {
      logger.info('Object.keys(global.settings):', Object.keys(global.settings));
      if (global.settings._CCSettings) {
        logger.info('global.settings._CCSettings 存在:', true);
        logger.info('Object.keys(global.settings._CCSettings):', Object.keys(global.settings._CCSettings));
      }
      if (global.settings.CCSettings) {
        logger.info('global.settings.CCSettings 存在:', true);
        logger.info('Object.keys(global.settings.CCSettings):', Object.keys(global.settings.CCSettings));
      }
    } else {
      logger.error('警告: global.settings 为空！');
    }
    
    // 处理 bundle 文件 - 直接扫描目录中的所有 index.*.js 文件
    logger.info('开始处理 bundle 文件...');
    await processBundleFiles(sourcePath, outputPath);
    logger.info('bundle 文件处理完成，继续执行后续步骤...');
    
    // 开始处理
    logger.info('开始分析代码...');
    await codeAnalyzer.analyze(code);
    logger.info('代码分析完成，继续执行后续步骤...');
    
    logger.info('开始处理资源...');
    await resourceProcessor.processResources();
    logger.info('资源处理完成，继续执行后续步骤...');
    
    logger.info('生成项目文件...');
    await projectGenerator.generateProject();
    logger.info('项目文件生成完成，继续执行后续步骤...');
    
    // 清理临时文件
    if (!verbose) {
      logger.info('清理临时文件...');
      await fileManager.cleanDirectory(tempPath);
    }
    
    logger.success('========================================');
    logger.success('逆向工程完成！');
    logger.success('========================================');
    return true;
  } catch (err) {
    logger.error('处理项目文件时出错:', err);
    throw err;
  }
}

/**
 * 处理 bundle 文件
 * @param {string} sourcePath 源项目路径
 * @param {string} outputPath 输出路径
 * @returns {Promise<void>}
 */
async function processBundleFiles(sourcePath, outputPath) {
  try {
    logger.info('扫描 bundle 文件...');
    const bundleFiles = [];
    
    // 递归扫描目录中的所有 index.*.js 文件
    function scanDirectory(directory) {
      try {
        const files = fs.readdirSync(directory);
        for (const file of files) {
          const fullPath = path.resolve(directory, file);
          const stat = fs.statSync(fullPath);
          
          if (stat.isDirectory()) {
            // 递归扫描子目录
            scanDirectory(fullPath);
          } else if (file.match(/^index\.[a-f0-9]+\.js$/)) {
            // 找到 bundle 文件
            const bundleName = `bundle_${file.split('.')[1]}`; // 使用哈希值作为 bundle 名称
            bundleFiles.push({
              name: bundleName,
              path: fullPath,
              hash: file.split('.')[1]
            });
            logger.debug(`找到 bundle 文件: ${bundleName} -> ${fullPath}`);
          }
        }
      } catch (err) {
        logger.error(`扫描目录 ${directory} 时出错:`, err);
      }
    }
    
    // 开始扫描
    scanDirectory(sourcePath);
    
    if (bundleFiles.length === 0) {
      logger.warn('未找到任何 bundle 文件');
      return;
    }
    
    logger.info(`找到 ${bundleFiles.length} 个 bundle 文件，开始分析...`);
    
    // 分析每个 bundle 文件（限制只处理前 3 个，以便测试后续流程）
    const maxBundlesToProcess = 3;
    logger.info(`限制处理前 ${maxBundlesToProcess} 个 bundle 文件...`);
    for (let i = 0; i < Math.min(bundleFiles.length, maxBundlesToProcess); i++) {
      const bundle = bundleFiles[i];
      logger.info(`分析 bundle 文件 ${i+1}/${maxBundlesToProcess}: ${bundle.name}`);
      try {
        const bundleContent = await readFile(bundle.path, 'utf-8');
        logger.debug(`bundle 文件大小: ${bundleContent.length} 字节`);
        await codeAnalyzer.analyze(bundleContent);
        logger.info(`bundle 文件 ${bundle.name} 分析完成`);
      } catch (err) {
        logger.error(`分析 bundle 文件 ${bundle.name} 时出错:`, err);
        // 继续处理下一个 bundle 文件，而不是中断整个流程
      }
    }
    
    logger.info(`已处理 ${Math.min(bundleFiles.length, maxBundlesToProcess)} 个 bundle 文件，剩余 ${Math.max(0, bundleFiles.length - maxBundlesToProcess)} 个未处理`);
    logger.info('所有 bundle 文件分析完成');
  } catch (err) {
    logger.error('处理 bundle 文件时出错:', err);
    // 不要抛出错误，以便工具可以继续执行后续步骤
    logger.warn('bundle 文件处理失败，继续执行后续步骤...');
  }
}

/**
 * 检测Cocos Creator项目版本并返回相应的文件路径
 * @param {string} sourcePath 源项目路径
 * @param {string} versionHint 版本提示
 * @returns {Object} 包含版本信息和文件路径的对象
 */
function detectProjectVersion(sourcePath, versionHint) {
  // 查找匹配模式的文件
  function findFileByPattern(directory, pattern) {
    try {
      const files = fs.readdirSync(directory);
      for (const file of files) {
        if (pattern.test(file)) {
          return path.resolve(directory, file);
        }
      }
    } catch (err) {
      // 目录不存在，返回null
    }
    return null;
  }

  // 2.4.x版本的可能路径
  const paths24x = {
    // 2.4.x 主要检查build目录下的文件
    settings: [
      // 优先检查src目录下的settings文件
      path.resolve(sourcePath, 'src/settings.js'),
      findFileByPattern(path.resolve(sourcePath, 'src'), /^settings\.[a-f0-9]+\.js$/),
      // 然后检查根目录下的文件
      path.resolve(sourcePath, 'settings.js'),
      findFileByPattern(sourcePath, /^settings\.[a-f0-9]+\.js$/),
      // 最后才检查main.js作为备选
      path.resolve(sourcePath, 'main.js'),
      findFileByPattern(sourcePath, /^main\.[a-f0-9]+\.js$/)
    ],
    project: [
      path.resolve(sourcePath, 'project.js'),
      path.resolve(sourcePath, 'main.js'),
      path.resolve(sourcePath, 'src/project.js'),
      // 支持带哈希值的文件名
      findFileByPattern(sourcePath, /^project\.[a-f0-9]+\.js$/),
      findFileByPattern(sourcePath, /^main\.[a-f0-9]+\.js$/),
      findFileByPattern(path.resolve(sourcePath, 'src'), /^project\.[a-f0-9]+\.js$/)
    ],
    res: [
      path.resolve(sourcePath, 'assets'),
      path.resolve(sourcePath, 'res'),
      path.resolve(sourcePath, 'src/assets')
    ]
  };

  // 2.3.x及以下版本的路径
  const paths23x = {
    settings: [
      path.resolve(sourcePath, 'src/settings.js'),
      // 支持带哈希值的文件名
      findFileByPattern(path.resolve(sourcePath, 'src'), /^settings\.[a-f0-9]+\.js$/)
    ],
    project: [
      path.resolve(sourcePath, 'src/project.js'),
      // 支持带哈希值的文件名
      findFileByPattern(path.resolve(sourcePath, 'src'), /^project\.[a-f0-9]+\.js$/)
    ],
    res: [path.resolve(sourcePath, 'res')]
  };

  // 过滤掉null值
  function filterNull(arr) {
    return arr.filter(item => item !== null);
  }

  // 检测文件存在性并确定版本
  function findExistingPath(pathArray) {
    const filteredPaths = filterNull(pathArray);
    for (const filePath of filteredPaths) {
      if (fs.existsSync(filePath)) {
        // 检查是否为目录且不为空
        try {
          const stat = fs.statSync(filePath);
          if (stat.isDirectory()) {
            const files = fs.readdirSync(filePath);
            if (files.length > 0) {
              return filePath;
            }
          } else {
            // 如果是文件，直接返回
            return filePath;
          }
        } catch (err) {
          // 目录访问错误，跳过
        }
      }
    }
    return null;
  }

  // 如果用户提供了版本提示，优先使用对应版本的路径
  if (versionHint === '2.4.x') {
    const settings24 = findExistingPath(paths24x.settings);
    const project24 = findExistingPath(paths24x.project);
    const res24 = findExistingPath(paths24x.res);
    
    if (settings24 && project24 && res24) {
      logger.info('使用用户指定的Cocos Creator 2.4.x项目结构');
      return {
        version: '2.4.x',
        settingsPath: settings24,
        projectPath: project24,
        resPath: res24
      };
    } else {
      logger.warn('用户指定2.4.x版本，但未找到对应文件结构，尝试自动检测...');
    }
  } else if (versionHint === '2.3.x') {
    const settings23 = findExistingPath(paths23x.settings);
    const project23 = findExistingPath(paths23x.project);
    const res23 = findExistingPath(paths23x.res);
    
    if (settings23 && project23 && res23) {
      logger.info('使用用户指定的Cocos Creator 2.3.x项目结构');
      return {
        version: '2.3.x',
        settingsPath: settings23,
        projectPath: project23,
        resPath: res23
      };
    } else {
      logger.warn('用户指定2.3.x版本，但未找到对应文件结构，尝试自动检测...');
    }
  }

  // 自动检测：先尝试2.3.x路径（更精确的检测）
  const settings23 = findExistingPath(paths23x.settings);
  const project23 = findExistingPath(paths23x.project);
  const res23 = findExistingPath(paths23x.res);

  if (settings23 && project23 && res23) {
    logger.info('自动检测到Cocos Creator 2.3.x或更早版本项目结构');
    return {
      version: '2.3.x',
      settingsPath: settings23,
      projectPath: project23,
      resPath: res23
    };
  }

  // 再尝试2.4.x路径
  const settings24 = findExistingPath(paths24x.settings);
  const project24 = findExistingPath(paths24x.project);
  const res24 = findExistingPath(paths24x.res);

  if (settings24 && project24 && res24) {
    logger.info('自动检测到Cocos Creator 2.4.x项目结构');
    return {
      version: '2.4.x',
      settingsPath: settings24,
      projectPath: project24,
      resPath: res24
    };
  }

  // 如果都找不到，抛出详细错误信息
  throw new Error(`无法检测到有效的Cocos Creator项目结构，请检查输入路径是否正确。
支持的文件结构：
2.4.x: main.js/settings.js + project.js/main.js + assets/res目录
2.3.x: src/settings.js + src/project.js + res目录
也支持带哈希值的文件名，如main.123abc.js`);
}

/**
 * 验证路径是否存在
 * @param {string} resPath 资源路径
 * @param {string} settingsPath 设置文件路径
 * @param {string} projectPath 项目文件路径
 */
function validatePaths(resPath, settingsPath, projectPath) {
  if (!fs.existsSync(resPath)) {
    throw new Error(`错误: 资源路径不存在: ${resPath}`);
  }
  
  if (!fs.existsSync(settingsPath)) {
    throw new Error(`错误: settings.js 文件不存在: ${settingsPath}`);
  }
  
  if (!fs.existsSync(projectPath)) {
    throw new Error(`错误: project.js 文件不存在: ${projectPath}`);
  }
}

/**
 * 解析设置文件
 * @param {Buffer} settings 设置文件内容
 */
function parseSettings(settings) {
  try {
    const settingsContent = settings.toString('utf-8');
    logger.info('设置文件内容长度:', settingsContent.length);
    logger.info('设置文件内容前 200 字符:', settingsContent.substring(0, 200));
    
    // 直接尝试解析 _CCSettings 格式
    if (settingsContent.includes('window._CCSettings')) {
      logger.info('检测到 window._CCSettings 格式');
      // 尝试多种解析方法
      try {
        // 方法1: 在窗口对象中执行（最可靠的方法）
        logger.info('尝试方法1: 在窗口对象中执行');
        const result = eval("let window = {}; " + settingsContent + "; window");
        logger.info('方法1执行结果:', result);
        logger.info('方法1执行结果是否有_CCSettings:', result && result._CCSettings);
        if (result && result._CCSettings) {
          global.settings = result;
          global.settings.CCSettings = result._CCSettings;
          logger.info('成功解析 _CCSettings 格式');
          logger.info('解析结果包含的键:', Object.keys(result._CCSettings));
          return;
        } else {
          logger.error('方法1执行成功但没有找到_CCSettings');
        }
      } catch (e1) {
        logger.error('方法1失败:', e1.message);
        
        try {
          // 方法2: 提取 _CCSettings 部分
          logger.info('尝试方法2: 提取 _CCSettings 部分');
          const settingsMatch = settingsContent.match(/window\._CCSettings\s*=\s*({[^;]+});/);
          if (settingsMatch && settingsMatch[1]) {
            const settingsJson = settingsMatch[1];
            logger.info('提取的 _CCSettings 长度:', settingsJson.length);
            logger.info('提取的 _CCSettings 前 100 字符:', settingsJson.substring(0, 100));
            const _CCSettings = JSON.parse(settingsJson);
            global.settings = {
              _CCSettings: _CCSettings,
              CCSettings: _CCSettings
            };
            logger.info('成功解析 _CCSettings 格式');
            logger.info('解析结果包含的键:', Object.keys(_CCSettings));
            return;
          } else {
            logger.error('方法2: 未找到匹配的_CCSettings内容');
          }
        } catch (e2) {
          logger.error('方法2失败:', e2.message);
          
          try {
            // 方法3: 简化的提取方法
            logger.info('尝试方法3: 简化的提取方法');
            const startIdx = settingsContent.indexOf('{');
            const endIdx = settingsContent.lastIndexOf('}');
            if (startIdx !== -1 && endIdx !== -1) {
              const settingsJson = settingsContent.substring(startIdx, endIdx + 1);
              logger.info('提取的 JSON 长度:', settingsJson.length);
              const _CCSettings = JSON.parse(settingsJson);
              global.settings = {
                _CCSettings: _CCSettings,
                CCSettings: _CCSettings
              };
              logger.info('成功解析 _CCSettings 格式');
              logger.info('解析结果包含的键:', Object.keys(_CCSettings));
              return;
            } else {
              logger.error('方法3: 无法找到JSON对象边界');
            }
          } catch (e3) {
            logger.error('方法3失败:', e3.message);
          }
        }
      }
    }
    
    // 根据版本使用不同的解析方式
    if (global.cocosVersion === '2.4.x') {
      logger.info('使用 Cocos Creator 2.4.x 解析逻辑');
      // 2.4.x版本的解析逻辑
      if (settingsContent.includes('window.CCSettings')) {
        logger.info('检测到 window.CCSettings 格式');
        // 标准的CCSettings格式
        let _ccsettings = "let window = {CCSettings: {}};" + settingsContent.split(';')[0];
        global.settings = eval(_ccsettings);
        logger.info('解析结果包含的键:', Object.keys(global.settings.CCSettings));
      } else {
        // 尝试直接解析为对象
        try {
          logger.info('尝试直接解析设置文件');
          global.settings = eval("let window = {}; " + settingsContent + "; window");
          logger.info('解析结果包含的键:', Object.keys(global.settings));
        } catch (e) {
          logger.error('2.4.x设置文件解析失败，使用默认设置:', e.message);
          global.settings = { CCSettings: {} };
        }
      }
    } else {
      logger.info('使用 Cocos Creator 2.3.x 解析逻辑');
      // 2.3.x及以下版本的原有解析逻辑
      let _ccsettings = "let window = {CCSettings: {}};" + settingsContent.split(';')[0];
      global.settings = eval(_ccsettings);
      logger.info('解析结果包含的键:', Object.keys(global.settings.CCSettings));
    }
    
    // 确保settings不为空
    if (!global.settings) {
      logger.error('警告: global.settings 为空，使用默认设置');
      global.settings = { CCSettings: {} };
    } else if (!global.settings.CCSettings && !global.settings._CCSettings) {
      logger.error('警告: global.settings 中没有找到 CCSettings 或 _CCSettings，使用默认设置');
      global.settings = { CCSettings: {} };
    } else {
      logger.info('设置解析成功，最终结果:');
      logger.info('global.settings 包含的键:', Object.keys(global.settings));
      if (global.settings.CCSettings) {
        logger.info('global.settings.CCSettings 包含的键:', Object.keys(global.settings.CCSettings));
      }
      if (global.settings._CCSettings) {
        logger.info('global.settings._CCSettings 包含的键:', Object.keys(global.settings._CCSettings));
      }
    }
    
    if (global.verbose) {
      logger.info('已加载项目设置:', Object.keys(global.settings));
      if (global.settings._CCSettings) {
        logger.info('已加载 _CCSettings:', Object.keys(global.settings._CCSettings));
      }
      if (global.settings.CCSettings) {
        logger.info('已加载 CCSettings:', Object.keys(global.settings.CCSettings));
      }
    }
  } catch (err) {
    logger.error('解析设置文件时出错:', err);
    logger.warn('使用默认设置');
    global.settings = { CCSettings: {} };
  }
}

module.exports = { reverseProject }; 