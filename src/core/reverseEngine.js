/*
 * @Date: 2025-06-07 10:06:12
 * @Description: Cocos Creator 逆向工程核心引擎
 */
const fs = require('fs');
const path = require('path');
const { promisify } = require('util');
const parser = require('@babel/parser');
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
  const { sourcePath, outputPath, verbose = false, versionHint, originalStructure, bundleConcurrency } = options;
  
  // 全局配置初始化
  global.config = loadConfig();
  // 覆盖并发参数（优先使用 CLI 传入）
  if (!global.config.advanced) global.config.advanced = {};
  if (bundleConcurrency && Number.isFinite(bundleConcurrency)) {
    global.config.advanced.bundleConcurrency = Math.max(1, Number(bundleConcurrency));
  }
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
  
  
    // 自动检测原始项目的 library 目录（如果未通过 --original-structure 指定）
    let finalOriginalStructure = originalStructure;
    if (!finalOriginalStructure) {
      // 尝试从源项目的父级或上两级找到 library 目录
      const parentDir = path.dirname(sourcePath);
      const candidates = [
        path.join(parentDir, 'library'),
        path.resolve(parentDir, '..', 'library')
      ];
      for (const libPath of candidates) {
        if (fs.existsSync(libPath) && fs.statSync(libPath).isDirectory()) {
          // originalStructureRoot 设为项目根（library 的父级），便于直接访问 assets 目录
          finalOriginalStructure = path.dirname(libPath);
          logger.info(`自动检测到原始项目 library 目录: ${libPath}`);
          break;
        }
      }
    }
  
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
      ast: astPath,
      originalStructureRoot: finalOriginalStructure ? path.resolve(finalOriginalStructure) : ''
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
    // 开始处理
    logger.info('开始分析代码...');
    await codeAnalyzer.analyze(code);
    logger.info('代码分析完成，继续执行后续步骤...');
    
    logger.info('开始处理资源...');
    await resourceProcessor.processResources();
    logger.info('资源处理完成，继续执行后续步骤...');

    // 优先从原始源代码目录复制脚本（在所有其他处理之后，确保覆盖混淆代码）
    logger.info('检查并复制原始源代码文件...');
    await copySourceScripts(sourcePath, outputPath);
    logger.info('原始源代码复制步骤完成');

    // 复制原始资源文件（场景、prefab、纹理等，如果存在的话）
    logger.info('检查并复制原始资源文件...');
    await copyOriginalResources(sourcePath, outputPath);
    logger.info('原始资源复制步骤完成');
    
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

    // 并发控制（默认 1，避免文件写入冲突，可在配置 advanced.bundleConcurrency 或 advanced.maxParallel 调整）
    const limit = Math.max(1, Number((global.config && global.config.advanced && (global.config.advanced.bundleConcurrency || global.config.advanced.maxParallel)) || 1));
    logger.info(`使用并发数: ${limit}`);

    // 将数组分块按并发执行
    const chunks = [];
    for (let i = 0; i < bundleFiles.length; i += limit) {
      chunks.push(bundleFiles.slice(i, i + limit));
    }

    let processed = 0;
    for (let ci = 0; ci < chunks.length; ci++) {
      const chunk = chunks[ci];
      await Promise.all(chunk.map(async (bundle, idx) => {
        const overallIndex = processed + idx + 1;
        logger.info(`分析 bundle 文件 ${overallIndex}/${bundleFiles.length}: ${bundle.name}`);
        try {
          const bundleContent = await readFile(bundle.path, 'utf-8');
          logger.debug(`bundle 文件大小: ${bundleContent.length} 字节`);
          await codeAnalyzer.analyze(bundleContent);
          logger.info(`bundle 文件 ${bundle.name} 分析完成`);
        } catch (err) {
          logger.error(`分析 bundle 文件 ${bundle.name} 时出错:`, err);
        }
      }));
      processed += chunk.length;
    }

    logger.info(`已处理 ${processed} 个 bundle 文件`);
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
    const content = settings.toString('utf-8');
    logger.info('解析 settings.js（AST 模式，无 eval）');

    const ast = parser.parse(content, {
      sourceType: 'script'
    });

    // 收集形如 const _CCSettings = {...} 的变量
    const varMap = new Map();
    let picked = null;

    function toPlain(node) {
      if (!node) return undefined;
      switch (node.type) {
        case 'NullLiteral':
          return null;
        case 'BooleanLiteral':
        case 'StringLiteral':
        case 'NumericLiteral':
          return node.value;
        case 'ObjectExpression': {
          const obj = {};
          for (const prop of node.properties || []) {
            if (prop.type !== 'ObjectProperty') continue;
            const key = prop.key.type === 'Identifier' ? prop.key.name : String(prop.key.value);
            obj[key] = toPlain(prop.value);
          }
          return obj;
        }
        case 'ArrayExpression':
          return node.elements.map(el => toPlain(el));
        case 'Identifier': {
          // 若引用到之前收集的纯对象变量
          if (varMap.has(node.name)) return varMap.get(node.name);
          // 常见字面值标识符容错
          if (node.name === 'undefined') return undefined;
          return undefined;
        }
        default:
          return undefined;
      }
    }

    for (const stmt of ast.program.body) {
      if (stmt.type === 'VariableDeclaration') {
        for (const d of stmt.declarations) {
          if (d.id && d.id.type === 'Identifier' && d.init && d.init.type === 'ObjectExpression') {
            const name = d.id.name;
            if (name === '_CCSettings' || name === 'CCSettings') {
              const obj = toPlain(d.init);
              if (obj) {
                varMap.set(name, obj);
                picked = picked || obj;
              }
            } else {
              // 其他对象也缓存，供 Identifier 解析
              const obj = toPlain(d.init);
              if (obj) varMap.set(name, obj);
            }
          }
        }
      } else if (stmt.type === 'ExpressionStatement' && stmt.expression.type === 'AssignmentExpression') {
        const assign = stmt.expression;
        const left = assign.left;
        const right = assign.right;
        // window._CCSettings = {...} 或 window.CCSettings = {...}
        if (left.type === 'MemberExpression' && !left.computed) {
          const obj = left.object;
          const prop = left.property;
          const objName = obj.type === 'Identifier' ? obj.name : '';
          const propName = prop.type === 'Identifier' ? prop.name : '';
          if (objName === 'window' && (propName === '_CCSettings' || propName === 'CCSettings')) {
            let value = toPlain(right);
            // 右侧可能是标识符，尝试从 varMap 解析
            if (value === undefined && right.type === 'Identifier' && varMap.has(right.name)) {
              value = varMap.get(right.name);
            }
            if (value) {
              picked = picked || value;
            }
          }
        }
      }
    }

    if (!picked && varMap.has('_CCSettings')) picked = varMap.get('_CCSettings');
    if (!picked && varMap.has('CCSettings')) picked = varMap.get('CCSettings');

    if (!picked) {
      logger.warn('未在 settings.js 中解析到 _CCSettings/CCSettings，使用空设置');
      global.settings = { CCSettings: {} };
      return;
    }

    global.settings = { _CCSettings: picked, CCSettings: picked };
    logger.info('settings 解析成功，键数量: ' + Object.keys(picked || {}).length);
  } catch (err) {
    logger.error('解析设置文件时出错（AST）:', err);
    logger.warn('使用默认设置');
    global.settings = { CCSettings: {} };
  }
}

/**
 * 从原始源代码目录复制脚本文件
 * @param {string} sourcePath 源项目路径（build/web-mobile）
 * @param {string} outputPath 输出路径
 * @returns {Promise<void>}
 */
async function copySourceScripts(sourcePath, outputPath) {
  try {
    // 检查原始源代码目录是否存在
    // sourcePath 通常是 C:\...\build\web-mobile
    // 源代码目录通常在 C:\...\assets\script（与 build 同级）
    const parentDir = path.dirname(path.dirname(sourcePath));  // 获取项目根目录
    const sourceScriptsDir = path.join(parentDir, 'assets', 'script');
    
    if (!fs.existsSync(sourceScriptsDir)) {
      logger.debug(`原始源代码目录不存在: ${sourceScriptsDir}`);
      return;
    }

    logger.info(`发现原始源代码目录: ${sourceScriptsDir}`);

    // 先清除输出目录中的 Scripts 文件夹（删除之前生成的混淆代码）
    const outputScriptsDir = path.join(outputPath, 'assets', 'Scripts');
    if (fs.existsSync(outputScriptsDir)) {
      logger.debug('清除旧的 Scripts 目录...');
      fs.rmSync(outputScriptsDir, { recursive: true, force: true });
    }

    // 递归复制脚本文件
    function copyScripts(sourceDir, targetDir) {
      try {
        if (!fs.existsSync(targetDir)) {
          fs.mkdirSync(targetDir, { recursive: true });
        }

        const files = fs.readdirSync(sourceDir);
        for (const file of files) {
          const srcPath = path.join(sourceDir, file);
          const stat = fs.statSync(srcPath);

          if (stat.isDirectory()) {
            // 递归复制子目录
            const subTargetDir = path.join(targetDir, file);
            copyScripts(srcPath, subTargetDir);
          } else if (file.endsWith('.ts') || file.endsWith('.js')) {
            // 复制脚本文件
            const tgtPath = path.join(targetDir, file);
            const content = fs.readFileSync(srcPath, 'utf-8');
            fs.writeFileSync(tgtPath, content, 'utf-8');
            if (global.verbose) {
              logger.debug(`复制源代码文件: ${file}`);
            }
          } else if (file.endsWith('.meta')) {
            // 复制所有 .meta 文件（包括脚本文件的 meta 和目录的 meta）
            const tgtPath = path.join(targetDir, file);
            const content = fs.readFileSync(srcPath, 'utf-8');
            fs.writeFileSync(tgtPath, content, 'utf-8');
          }
        }
      } catch (err) {
        logger.error(`复制脚本文件时出错: ${err.message}`);
      }
    }

    copyScripts(sourceScriptsDir, outputScriptsDir);
    logger.info('原始源代码复制完成');
  } catch (err) {
    logger.error('复制源代码脚本时出错:', err);
  }
}

/**
 * 复制原始资源文件（场景、prefab、纹理等）
 * @param {string} sourcePath - 源路径（build/web-mobile）
 * @param {string} outputPath - 输出路径
 */
async function copyOriginalResources(sourcePath, outputPath) {
  try {
    // 获取项目根目录
    const projectRoot = path.dirname(path.dirname(sourcePath));
    const originalAssetsDir = path.join(projectRoot, 'assets');
    
    if (!fs.existsSync(originalAssetsDir)) {
      logger.debug(`原始资源目录不存在: ${originalAssetsDir}`);
      return;
    }

    logger.info(`发现原始资源目录: ${originalAssetsDir}`);

    // 递归复制资源文件（除了 script 目录，因为已经单独处理了）
    function copyAssets(sourceDir, targetDir) {
      try {
        if (!fs.existsSync(targetDir)) {
          fs.mkdirSync(targetDir, { recursive: true });
        }

        const files = fs.readdirSync(sourceDir);
        for (const file of files) {
          // 跳过 script 目录（已单独处理）
          if (file === 'script' || file === 'script.meta') {
            continue;
          }

          const srcPath = path.join(sourceDir, file);
          const stat = fs.statSync(srcPath);

          if (stat.isDirectory()) {
            // 递归复制子目录
            const subTargetDir = path.join(targetDir, file);
            copyAssets(srcPath, subTargetDir);
          } else {
            // 只复制需要的文件类型
            const ext = path.extname(file).toLowerCase();
            if (['.fire', '.prefab', '.png', '.jpg', '.jpeg', '.gif', '.webp', 
                  '.anim', '.animation', '.fx', '.effect', '.atlas', '.meta'].includes(ext)) {
              const tgtPath = path.join(targetDir, file);
              
              // 检查目标文件是否已存在（优先保留已有的生成版本）
              if (!fs.existsSync(tgtPath)) {
                // 区分文本文件和二进制文件
                const isTextFile = ['.fire', '.prefab', '.anim', '.animation', '.meta'].includes(ext);
                
                if (isTextFile) {
                  // 文本文件使用 UTF-8 编码
                  const content = fs.readFileSync(srcPath, 'utf-8');
                  fs.writeFileSync(tgtPath, content, 'utf-8');
                } else {
                  // 图片和二进制文件直接复制（不进行编码转换）
                  fs.copyFileSync(srcPath, tgtPath);
                }
                
                if (global.verbose) {
                  logger.debug(`复制资源文件: ${file}`);
                }
              }
            }
          }
        }
      } catch (err) {
        logger.error(`复制资源文件时出错: ${err.message}`);
      }
    }

    const outputAssetsDir = path.join(outputPath, 'assets');
    copyAssets(originalAssetsDir, outputAssetsDir);
    logger.info('原始资源复制完成');
  } catch (err) {
    logger.error('复制原始资源时出错:', err);
  }
}

module.exports = { reverseProject }; 