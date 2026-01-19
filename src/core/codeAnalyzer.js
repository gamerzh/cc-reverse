/*
 * @Date: 2025-06-07 10:06:12
 * @Description: 代码分析和生成工具
 */
const generator = require("@babel/generator");
const parser = require("@babel/parser");
const traverse = require("@babel/traverse");
const types = require("@babel/types");
const fs = require("fs");
const path = require("path");
const { promisify } = require('util');
const { uuidUtils } = require('../utils/uuidUtils');
const { fileManager } = require('../utils/fileManager');
const { logger } = require('../utils/logger');

// 将 fs 的异步方法转换为 Promise
const mkdir = promisify(fs.mkdir);
const writeFile = promisify(fs.writeFile);
const appendFile = promisify(fs.appendFile);

/**
 * 代码分析器模块
 */
const codeAnalyzer = {
    // 记录模块的 uuid 与可读名，便于还原脚本目录
    moduleInfo: new Map(),
    /**
     * 分析编译源代码
     * @param {string} code 要分析的源代码
     * @returns {Promise<void>}
     */
    async analyze(code) {
        try {
            // 1. 解析代码为 AST
            const ast = parser.parse(code, {
                sourceType: 'module',
                allowImportExportEverywhere: true,
                allowReturnOutsideFunction: true,
                plugins: [
                    'jsx',
                    'typescript',
                    'decorators-legacy',
                    'classProperties',
                    'objectRestSpread'
                ]
            });
            const values = [];
            // 本次分析的模块信息缓存
            this.moduleInfo = new Map();
            const moduleInfo = this.moduleInfo;
            
            // 2. 定义访问者函数查找值
            const findValue = {
                ArrayExpression(path) {
                    const { node } = path;
                    if (node && node.elements) {
                        for (let i of node.elements) {
                            if (types.isStringLiteral(i)) {
                                values.push(i.value);
                            }
                        }
                    }
                },
            };
            
            // 辅助函数 - 处理模块参数
            const processModuleParams = function(node) {
                try {
                    if (!node || !node.value || !node.value.elements || !node.value.elements[0]) return null;
                    const fn = node.value.elements[0];
                    const params = Array.isArray(fn.params) ? fn.params : [];

                    const getName = (p, fallback) => (p && p.type === 'Identifier' && p.name) ? p.name : fallback;
                    const _require = getName(params[0], '_require');
                    const _module = getName(params[1], '_module');
                    const _exports = getName(params[2], '_exports');

                    // 若 body 不存在则跳过
                    if (!fn.body || !fn.body.body) return { _require, _module, _exports };

                    // 创建变量声明
                    const id1 = types.identifier(`${_require}`);
                    const id2 = types.identifier(`${_module}`);
                    const id3 = types.identifier(`${_exports}`);
                    const init1 = types.identifier("require");
                    const init2 = types.identifier("module");
                    const init3 = types.identifier("exports");
                    const variable1 = types.variableDeclarator(id1, init1);
                    const declaration1 = types.variableDeclaration("let", [variable1]);
                    const variable2 = types.variableDeclarator(id2, init2);
                    const declaration2 = types.variableDeclaration("let", [variable2]);
                    const variable3 = types.variableDeclarator(id3, init3);
                    const declaration3 = types.variableDeclaration("let", [variable3]);

                    // 将声明添加到节点
                    fn.body.body.unshift(declaration1, declaration2, declaration3);

                    return { _require, _module, _exports };
                } catch (e) {
                    logger.debug('跳过 processModuleParams，节点结构不符合预期');
                    return null;
                }
            };
            
            // 辅助函数 - 生成元数据文件
            const recordModuleInfo = function(moduleName, payload = {}) {
                if (!moduleName) return;
                const prev = moduleInfo.get(moduleName) || {};
                moduleInfo.set(moduleName, { ...prev, ...payload });
            };

            const generateMetaFiles = function(node, moduleName) {
                if (node.type == 'ExpressionStatement') {
                    // 处理表达式数组
                    if (node.expression.expressions) {
                        for (let a of node.expression.expressions) {
                            if (a.arguments && a.arguments.length == 3) {
                                if (a.arguments[1]) {
                                    if (a.arguments[1].type && a.arguments[1].type == "StringLiteral" && a.arguments[1].value != "__esModule") {
                                        const arg2 = a.arguments[2];
                                        const uuidRaw = a.arguments[1].value;
                                        if (!arg2 || !arg2.value || typeof arg2.value !== 'string') continue;
                                        recordModuleInfo(moduleName, { uuid: uuidRaw, scriptName: arg2.value });
                                    }
                                }
                            }
                        }
                    }
                    
                    // 处理单个表达式
                    if (node.expression.arguments && node.expression.arguments.length == 3) {
                        if (node.expression.arguments[1]) {                                        
                            if (node.expression.arguments[1].type && node.expression.arguments[1].type == "StringLiteral" && node.expression.arguments[1].value != "__esModule") {
                                const arg2 = node.expression.arguments[2];
                                const uuidRaw = node.expression.arguments[1].value;
                                if (!arg2 || !arg2.value || typeof arg2.value !== 'string') return;
                                recordModuleInfo(moduleName, { uuid: uuidRaw, scriptName: arg2.value });
                            }
                        }
                    }
                }
            };
            
            // 辅助函数 - 处理导入路径
            const processImportPaths = function(node) {
                // 处理变量声明中的导入路径
                if (node.type == 'VariableDeclaration' && node.declarations) {
                    for (let j of node.declarations) {
                        if (j.init) {
                            // 处理初始化表达式的参数
                            if (j.type == "VariableDeclarator" && j.init.arguments) {
                                if (j.init.arguments[0] && j.init.arguments[0].value) {
                                    j.init.arguments[0].value = path.basename(j.init.arguments[0].value);
                                }
                            }
                            
                            // 处理初始化表达式序列
                            if (j.type == "VariableDeclarator" && j.init.expressions) {
                                for (let res of j.init.expressions) {
                                    if (res.type == "CallExpression") {
                                        if (res.arguments && res.arguments[0] && res.arguments[0].value) {
                                            if (typeof res.arguments[0].value == "string") {
                                                res.arguments[0].value = path.basename(res.arguments[0].value);
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                
                // 处理表达式语句中的导入路径
                if (node.type == 'ExpressionStatement' && node.expression) {
                    if (node.expression.type == "CallExpression" && node.expression.arguments) {
                        let res = node.expression.arguments;
                        if (res[0] && typeof res[0].value == "string") {
                            res[0].value = path.basename(res[0].value);
                        }
                    }
                }
            };
            
            // 辅助函数 - 保存 AST 到文件
            const saveAstToFile = async function(node, value) {
                try {
                    const str = JSON.stringify(node.value.elements[0].body);
                    const astPath = path.join(global.paths.ast, `${value}.json`);
                    
                    // 写入文件
                    await writeFile(astPath, str, { flag: 'w+' });
                    
                    if (global.verbose) {
                        logger.debug(`保存 AST 到文件: ${astPath}`);
                    }
                } catch (err) {
                    logger.error(`保存 AST 到文件时出错:`, err);
                }
            };
            
            // 辅助函数 - 处理节点元素
            const processNodeElements = async function(node, value) {
                if (!node || !node.value || !node.value.elements || !node.value.elements[0] || !node.value.elements[0].body || !node.value.elements[0].body.body) return;
                for (let i of node.value.elements[0].body.body) {
                    // 生成元数据文件
                    generateMetaFiles(i, value);
                    
                    // 处理导入路径
                    processImportPaths(i);
                }
                
                // 保存 AST 到文件
                await saveAstToFile(node, value);
            };
            
            // 3. 定义分割访问者 - 只包含合法的 Babel 访问器方法
            const splitVisitor = {
                Property(path) {
                    const { node } = path;
                    if (values.length > 0) {
                        for (let value of values) {
                            // 仅在 key 匹配且 value 结构符合数组且第一个元素具有函数体时处理
                            const keyName = node && node.key ? (node.key.name || node.key.value) : undefined;
                            const hasElements = node && node.value && Array.isArray(node.value.elements) && node.value.elements[0];
                            const first = hasElements ? node.value.elements[0] : null;
                            const hasFuncBody = first && first.body && first.body.body;
                            if (keyName === value && hasElements && hasFuncBody) {
                                // 处理模块参数 - 这里直接调用辅助函数
                                processModuleParams(node);
                                
                                // 处理节点元素 - 这里直接调用辅助函数（注意：这里不能使用 await，因为 Babel traverse 不支持异步）
                                // 改为同步处理或使用其他方式
                                try {
                                    // 同步处理节点元素
                                    for (let i of first.body.body) {
                                        // 生成元数据文件
                                        generateMetaFiles(i, value);
                                        
                                        // 处理导入路径
                                        processImportPaths(i);
                                    }
                                    
                                    // 同步保存 AST 到文件
                                    // 创建完整的 Program AST 以便后续正确生成代码
                                    const programAst = {
                                        type: 'Program',
                                        body: first.body.body,
                                        sourceType: 'module',
                                        directives: []
                                    };
                                    const str = JSON.stringify(programAst);
                                    const astPath = require('path').join(global.paths.ast, `${value}.json`);
                                    
                                    // 写入文件
                                    fs.writeFileSync(astPath, str, { flag: 'w+' });
                                    
                                    if (global.verbose) {
                                        logger.debug(`保存 AST 到文件: ${astPath}`);
                                    }
                                } catch (err) {
                                    logger.error(`处理节点元素时出错:`, err);
                                }
                            }
                        }
                    }
                }
            };
            
            // 遍历 AST
            traverse.default(ast, findValue);
            traverse.default(ast, splitVisitor);
            
            // 处理 AST 文件生成代码
            await this.processAstFiles();
            
            logger.info('代码分析完成');
        } catch (err) {
            logger.error('分析编译代码时出错:', err);
            throw err;
        }
    },
    
    /**
     * 处理 AST 文件生成代码
     */
    async processAstFiles() {
        try {
            // 检查 AST 目录是否存在
            if (!global.paths.ast) {
                logger.warn('AST 目录路径未设置');
                return;
            }

            // 尝试读取 AST 目录
            let astFiles = [];
            try {
                astFiles = await fileManager.readDirectory(global.paths.ast);
            } catch (err) {
                logger.warn(`读取 AST 目录失败: ${err.message}，跳过代码生成`);
                return;
            }

            if (!astFiles || astFiles.length === 0) {
                logger.debug('没有找到 AST 文件');
                return;
            }

            // 过滤出 JSON 文件
            const jsonFiles = astFiles.filter(f => f.endsWith('.json'));
            
            for (const file of jsonFiles) {
                const fullPath = path.join(global.paths.ast, file);
                try {
                    const content = await fileManager.readFile(fullPath);
                    const key = path.basename(file, '.json');
                    await this.generateCode(JSON.parse(content), key);
                } catch (err) {
                    logger.error(`处理 AST 文件 ${file} 时出错:`, err);
                }
            }
        } catch (err) {
            logger.error('处理 AST 文件时出错:', err);
            throw err;
        }
    },
    
    /**
     * 从 AST 生成代码
     * @param {Object} ast AST 对象
     * @param {string} filename 文件名
     */
    async generateCode(ast, filename) {
        try {
            // 生成代码：将 AST 转回源代码字符串
            const generated = generator.default(ast, {});
            let code = generated.code;
            
            if (!code || typeof code !== 'string') {
                logger.warn(`生成代码 ${filename} 时失败：无法获取有效的代码字符串`);
                return;
            }

            const outputInfo = this.resolveScriptOutput(filename);

            // 确保输出目录存在
            await mkdir(path.dirname(outputInfo.outputPath), { recursive: true });

            // 直接写入生成的代码
            await writeFile(
                outputInfo.outputPath,
                code,
                { encoding: "utf-8" }
            );

            // 生成元数据文件（路径与脚本一致）
            this.generateMetaFile(outputInfo.baseName, outputInfo.metaDir, outputInfo.uuid);

            if (global.verbose) {
                logger.debug(`生成代码文件: ${outputInfo.outputPath}`);
            }
        } catch (err) {
            logger.error(`生成代码 ${filename} 时出错:`, err);
        }
    },
    
    /**
     * 生成元数据文件
     * @param {string} baseName 文件名（含扩展名）
     * @param {string} metaDir 相对于 assets 的目录
     * @param {string} uuidCandidate 源 uuid
     */
    generateMetaFile(baseName, metaDir, uuidCandidate) {
        const metaUuid = this.resolveMetaUuid(uuidCandidate, baseName);
        const targetDir = metaDir && metaDir !== '.' ? metaDir : 'Scripts';
        const meta = {
            "ver": "1.0.8",
            "uuid": metaUuid,
            "isPlugin": false,
            "loadPluginInWeb": true,
            "loadPluginInNative": true,
            "loadPluginInEditor": false,
            "subMetas": {}
        };
        
        fileManager.writeFile(targetDir, baseName + ".meta", meta);
    },

    /**
     * 依据 _CCSettings.rawAssets 或原始信息恢复脚本输出路径
     * @param {string} filename 模块名（bundle 内部 key）
     * @returns {Object} 输出信息
     */
    resolveScriptOutput(filename) {
        const info = (this.moduleInfo && this.moduleInfo.get(filename)) || {};
        const uuidCandidate = info.uuid;
        const scriptName = info.scriptName || filename;

        // 尝试从 settings 中找到原始路径
        let settingsPath = '';
        if (uuidCandidate) {
            settingsPath = this.findScriptPathFromSettings(uuidCandidate);
        }
        
        let rel = settingsPath || `Scripts/${scriptName}`;
        rel = this.normalizeScriptRelativePath(rel);

        return {
            outputPath: path.join(global.paths.output, 'assets', ...rel.split('/')),
            metaDir: path.dirname(rel),
            baseName: path.basename(rel),
            uuid: uuidCandidate
        };
    },

    /**
     * 查找 _CCSettings.rawAssets 中脚本 uuid 对应的路径
     */
    findScriptPathFromSettings(uuidCandidate) {
        const settings = (global.settings && (global.settings._CCSettings || global.settings.CCSettings)) || {};
        const rawAssets = settings.rawAssets || {};
        const pools = [];
        if (rawAssets.assets) pools.push(rawAssets.assets);
        if (rawAssets.internal) pools.push(rawAssets.internal);

        const ids = this.expandUuidCandidates(uuidCandidate);
        for (const pool of pools) {
            for (const id of ids) {
                const entry = pool && pool[id];
                const url = this.extractAssetUrl(entry);
                if (url) return url;
            }
        }
        return '';
    },

    /**
     * 将 url 统一为 assets 相对路径并添加 .ts 扩展名
     */
    normalizeScriptRelativePath(rel) {
        if (!rel) rel = 'Scripts/unknown';
        rel = rel.replace(/^db:\/\//i, '');
        if (rel.toLowerCase().startsWith('assets/')) {
            rel = rel.slice(7);
        }
        rel = rel.replace(/^\/+/, '').replace(/\\/g, '/');
        if (!/\.ts$/i.test(rel) && !/\.js$/i.test(rel)) {
            rel = `${rel}.ts`;
        }
        // 若缺少目录信息，则放入 Scripts 根目录
        if (!rel.includes('/')) {
            rel = path.join('Scripts', rel).replace(/\\/g, '/');
        }
        return rel;
    },

    /**
     * 从 rawAssets 条目提取 URL
     */
    extractAssetUrl(entry) {
        if (!entry) return '';
        if (Array.isArray(entry)) return entry[0] || '';
        if (typeof entry === 'object') return entry.url || entry.path || entry.name || '';
        return '';
    },

    /**
     * 扩展 uuid 的多种表示，以便匹配 settings 键
     */
    expandUuidCandidates(id) {
        const set = new Set();
        if (id) set.add(id);
        try {
            const orig = uuidUtils.original_uuid(id);
            if (orig) set.add(orig);
        } catch (e) {
            // 忽略转换异常
        }
        try {
            const decoded = uuidUtils.decodeUuid(id);
            if (decoded) set.add(decoded);
        } catch (e) {
            // 忽略转换异常
        }
        return Array.from(set).filter(Boolean);
    },

    /**
     * 解析 meta uuid（优先使用 cc._RF 提供的 uuid）
     */
    resolveMetaUuid(uuidCandidate, baseName) {
        // 如果没有 uuid 候选，生成一个新的
        if (!uuidCandidate) {
            return uuidUtils.generateUuid();
        }

        const ids = this.expandUuidCandidates(uuidCandidate);
        for (const id of ids) {
            if (id && id.length > 0) {
                return id;
            }
        }
        
        // 如果所有都失败了，返回原始值或生成新的
        return uuidCandidate || uuidUtils.generateUuid();
    }
};

module.exports = { codeAnalyzer }; 