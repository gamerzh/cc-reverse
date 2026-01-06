/**
 * parse_bundle.js
 * Node.js分析器 - 负责理解代码，生成中间JSON
 */

const fs = require('fs-extra');
const path = require('path');
const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;
const prettier = require('prettier');
const esprima = require('esprima');

/**
 * 检测是否是Webpack bundle文件
 * @param {string} content - 文件内容
 * @returns {boolean} - 是否是Webpack bundle
 */
function isWebpackBundle(content) {
    // Webpack bundle的特征检测
    const webpackSignatures = [
        'webpackJsonp',
        'webpackChunk',
        'webpack_require',
        '/* webpack bootstrap */',
        'webpackPrefetch',
        'webpackPreload',
        '___webpack_exports__',
        'ModuleConcatenation bailout:',
        '/*! For license information please see',
        '//# sourceMappingURL='
    ];
    
    // 检测webpack签名
    for (const signature of webpackSignatures) {
        if (content.includes(signature)) {
            return true;
        }
    }
    
    // 检测模块定义模式
    const modulePatterns = [
        /\(function\s*\([^)]*\)\s*\{([\s\S]*?)\}\)\s*\([^)]*\);/, // 模块封装函数
        /\[\s*[^\]]+\s*\]|\{[^}]+\}/, // 模块映射
        /\d+\s*:\s*\(function\s*\([^)]*\)\s*\{/ // 模块定义
    ];
    
    let matchCount = 0;
    for (const pattern of modulePatterns) {
        if (pattern.test(content)) {
            matchCount++;
        }
    }
    
    return matchCount >= 2;
}

/**
 * 解析webpack bundle文件
 * @param {string} bundleContent - bundle文件内容
 * @returns {Array} - 提取的模块列表
 */
function parseWebpackBundle(bundleContent) {
    const modules = [];
    
    console.log('开始解析Webpack bundle...');
    
    try {
        // 查找webpack bootstrap和模块定义
        // Webpack 4/5 bundle的典型结构: (function(modules) { ... })({ moduleId: function(...) { ... }, ... })
        const bundlePattern = /\(function\s*\(modules\)\s*\{([\s\S]*?)\}\)\s*\(\s*(\{[^}]+\})\s*\);/;
        const bundleMatch = bundleContent.match(bundlePattern);
        
        if (bundleMatch) {
            const bootstrapCode = bundleMatch[1];
            const modulesObject = bundleMatch[2];
            
            console.log('找到Webpack bundle模块对象');
            
            // 解析模块对象
            let moduleMap;
            try {
                moduleMap = eval(`(${modulesObject})`);
            } catch (e) {
                console.error('无法直接解析模块对象，尝试正则匹配');
                // 正则匹配所有模块定义
                const modulePattern = /(\d+|"[^"\n]+"|'[^'\n]+')\s*:\s*\(function\s*\([^)]*\)\s*\{([\s\S]*?)\}\s*\)|\([^)]*\)\s*=>\s*\{([\s\S]*?)\}\s*\)/g;
                let match;
                let moduleCount = 0;
                
                while ((match = modulePattern.exec(modulesObject)) !== null) {
                    const moduleId = match[1].replace(/["']/g, '');
                    const moduleCode = match[2] || match[3];
                    
                    if (moduleCode) {
                        moduleCount++;
                        processModule(moduleId, moduleCode, modules);
                    }
                }
                
                console.log(`找到 ${moduleCount} 个Webpack模块`);
                return modules;
            }
            
            // 处理模块映射
            const moduleKeys = Object.keys(moduleMap);
            console.log(`找到 ${moduleKeys.length} 个Webpack模块`);
            
            moduleKeys.forEach(moduleId => {
                const moduleFactory = moduleMap[moduleId];
                if (typeof moduleFactory === 'function') {
                    // 提取函数体
                    const factoryStr = moduleFactory.toString();
                    const funcBodyMatch = factoryStr.match(/function\s*\([^)]*\)\s*\{([\s\S]*)\}/);
                    if (funcBodyMatch) {
                        const moduleCode = funcBodyMatch[1];
                        processModule(moduleId, moduleCode, modules);
                    }
                }
            });
        } else {
            // 尝试匹配其他Webpack bundle格式
            console.log('尝试匹配其他Webpack bundle格式');
            const alternativePattern = /\/\*\*\*\s*webpack\s*bootstrap\s*\*\*\*\/[\s\S]*?\/\*\*\/\s*([\w\W]*?);\s*\/\*\*\/\s*\/\*\*\//;
            const altMatch = bundleContent.match(alternativePattern);
            
            if (altMatch) {
                const bootstrapContent = altMatch[1];
                const moduleDefPattern = /\d+\s*:\s*\(function\s*\([^)]*\)\s*\{([\s\S]*?)\}\s*\)/g;
                let match;
                let moduleCount = 0;
                
                while ((match = moduleDefPattern.exec(bootstrapContent)) !== null) {
                    const moduleCode = match[1];
                    moduleCount++;
                    processModule(moduleCount, moduleCode, modules);
                }
                
                console.log(`找到 ${moduleCount} 个Webpack模块`);
            }
        }
    } catch (error) {
        console.error('解析Webpack bundle失败:', error.message);
        
        // 尝试更简单的方法：查找所有可能的cc.Class定义
        console.log('尝试直接查找cc.Class定义...');
        const classDefs = extractAllCcClasses(bundleContent);
        if (classDefs.length > 0) {
            modules.push({
                module: 'webpack_bundle',
                imports: {},
                staticProperties: [],
                classDefinitions: classDefs,
                isWebpackModule: true
            });
            console.log(`找到 ${classDefs.length} 个cc.Class定义`);
        }
    }
    
    return modules;
}

/**
 * 处理单个Webpack模块
 * @param {string} moduleId - 模块ID
 * @param {string} moduleCode - 模块代码
 * @param {Array} modules - 模块列表
 */
function processModule(moduleId, moduleCode, modules) {
    try {
        // 分析模块代码
        const ast = parser.parse(moduleCode, {
            sourceType: 'module',
            plugins: ['jsx', 'typescript', 'objectRestSpread', 'classProperties']
        });
        
        // 提取模块信息
        const moduleInfo = analyzeModuleCode(ast, moduleCode);
        
        if (moduleInfo.classDefinitions.length > 0 || moduleInfo.staticProperties.length > 0) {
            moduleInfo.module = `module_${moduleId}`;
            moduleInfo.isWebpackModule = true;
            modules.push(moduleInfo);
            console.log(`找到Webpack模块 ${moduleId}，包含 ${moduleInfo.classDefinitions.length} 个cc.Class定义和 ${moduleInfo.staticProperties.length} 个静态属性`);
        }
    } catch (error) {
        // 如果解析失败，尝试使用esprima
        try {
            const ast = esprima.parseScript(moduleCode, {
                sourceType: 'module',
                loc: true,
                range: true
            });
            
            // 简单提取cc.Class定义
            const classDefs = extractCcClassesFromAst(ast, moduleCode);
            if (classDefs.length > 0) {
                modules.push({
                    module: `module_${moduleId}`,
                    imports: {},
                    staticProperties: [],
                    classDefinitions: classDefs,
                    isWebpackModule: true
                });
                console.log(`找到Webpack模块 ${moduleId}，包含 ${classDefs.length} 个cc.Class定义`);
            }
        } catch (e) {
            // 忽略无法解析的模块
            console.error(`无法解析模块 ${moduleId}:`, e.message);
        }
    }
}

/**
 * 分析模块代码，提取完整信息
 * @param {Object} ast - AST对象
 * @param {string} code - 原始代码
 * @returns {Object} - 模块信息
 */
function analyzeModuleCode(ast, code) {
    const moduleInfo = {
        module: '',
        imports: {},
        staticProperties: [],
        classDefinitions: []
    };
    
    // 提取cc.Class定义
    traverse(ast, {
        CallExpression(path) {
            const callee = path.node.callee;
            if (
                callee.type === 'MemberExpression' &&
                callee.object.type === 'Identifier' &&
                callee.object.name === 'cc' &&
                callee.property.type === 'Identifier' &&
                callee.property.name === 'Class'
            ) {
                const classDef = parseCcClassCall(path.node);
                if (classDef) {
                    moduleInfo.classDefinitions.push(classDef);
                }
            }
        }
    });
    
    // 提取cc._RF.push调用（Cocos Creator模块注册）
    traverse(ast, {
        CallExpression(path) {
            const callee = path.node.callee;
            
            // 检查是否是 cc._RF.push 调用
            if (
                callee.type === 'MemberExpression' &&
                callee.object.type === 'MemberExpression' &&
                callee.object.object.type === 'Identifier' &&
                callee.object.object.name === 'cc' &&
                callee.object.property.type === 'Identifier' &&
                callee.object.property.name === '_RF' &&
                callee.property.type === 'Identifier' &&
                callee.property.name === 'push'
            ) {
                const args = path.node.arguments;
                if (args.length > 2 && args[2].type === 'StringLiteral') {
                    const moduleName = args[2].value;
                    moduleInfo.module = moduleName;
                    console.log(`找到模块名: ${moduleName}`);
                }
            }
        }
    });
    
    // 提取静态属性赋值
    traverse(ast, {
        AssignmentExpression(path) {
            if (
                path.node.left.type === 'MemberExpression' &&
                path.node.left.object.type === 'Identifier' &&
                (path.node.left.object.name === 'e' || path.node.left.object.name === 'module')
            ) {
                const propName = path.node.left.property.name;
                if (propName && !moduleInfo.staticProperties.includes(propName)) {
                    moduleInfo.staticProperties.push(propName);
                }
            }
        }
    });
    
    return moduleInfo;
}

/**
 * 从AST中提取cc.Class定义
 * @param {Object} ast - AST对象
 * @param {string} code - 原始代码
 * @returns {Array} - cc.Class定义列表
 */
function extractCcClassesFromAst(ast, code) {
    const classDefs = [];
    
    // 简单的递归遍历AST查找cc.Class调用
    function traverseAst(node) {
        if (node.type === 'CallExpression') {
            let callee = node.callee;
            let isCcClass = false;
            
            // 检查是否是 cc.Class
            if (callee.type === 'MemberExpression') {
                if (callee.object.name === 'cc' && callee.property.name === 'Class') {
                    isCcClass = true;
                }
            }
            
            if (isCcClass && node.arguments.length > 0) {
                const classArg = node.arguments[0];
                if (classArg.type === 'ObjectExpression') {
                    // 提取类定义
                    const classDef = {
                        type: 'cc_class',
                        name: 'UnknownClass',
                        extends: 'cc.Component',
                        properties: [],
                        methods: []
                    };
                    
                    // 提取类属性
                    if (classArg.properties) {
                        classArg.properties.forEach(prop => {
                            if (prop.type === 'Property') {
                                const key = prop.key.name || prop.key.value;
                                if (key === 'name' && prop.value.type === 'Literal') {
                                    classDef.name = prop.value.value;
                                } else if (key === 'extends') {
                                    if (prop.value.type === 'Identifier') {
                                        classDef.extends = prop.value.name;
                                    } else if (prop.value.type === 'MemberExpression') {
                                        classDef.extends = extractMemberExprValue(prop.value);
                                    }
                                } else if (key === 'properties' && prop.value.type === 'ObjectExpression') {
                                    classDef.properties = parsePropertiesFromAst(prop.value);
                                } else if (prop.value.type === 'FunctionExpression' || prop.value.type === 'ArrowFunctionExpression') {
                                    // 方法
                                    const method = {
                                        name: key,
                                        params: [],
                                        type: prop.value.type === 'ArrowFunctionExpression' ? 'arrow' : 'function'
                                    };
                                    if (prop.value.params) {
                                        method.params = prop.value.params.map(p => p.name || 'arg');
                                    }
                                    classDef.methods.push(method);
                                }
                            }
                        });
                    }
                    
                    classDefs.push(classDef);
                }
            }
        }
        
        // 递归遍历子节点
        for (const key in node) {
            if (node[key] && typeof node[key] === 'object') {
                if (Array.isArray(node[key])) {
                    node[key].forEach(child => traverseAst(child));
                } else {
                    traverseAst(node[key]);
                }
            }
        }
    }
    
    traverseAst(ast);
    return classDefs;
}

/**
 * 提取成员表达式的值
 * @param {Object} node - 成员表达式节点
 * @returns {string} - 成员表达式值
 */
function extractMemberExprValue(node) {
    const parts = [];
    let current = node;
    while (current) {
        if (current.property && current.property.name) {
            parts.unshift(current.property.name);
        }
        if (current.object.type === 'Identifier') {
            parts.unshift(current.object.name);
            break;
        } else if (current.object.type === 'MemberExpression') {
            current = current.object;
        } else {
            break;
        }
    }
    return parts.join('.');
}

/**
 * 从AST解析属性定义
 * @param {Object} propNode - 属性节点
 * @returns {Array} - 属性列表
 */
function parsePropertiesFromAst(propNode) {
    const properties = [];
    
    if (propNode.properties) {
        propNode.properties.forEach(prop => {
            if (prop.type === 'Property') {
                const propName = prop.key.name || prop.key.value;
                const property = {
                    name: propName,
                    type: 'any',
                    defaultValue: null
                };
                
                if (prop.value.type === 'ObjectExpression') {
                    // 对象形式的属性定义
                    prop.value.properties.forEach(subProp => {
                        if (subProp.type === 'Property') {
                            const subKey = subProp.key.name || subProp.key.value;
                            if (subKey === 'type') {
                                if (subProp.value.type === 'Identifier') {
                                    property.type = subProp.value.name;
                                } else if (subProp.value.type === 'MemberExpression') {
                                    property.type = extractMemberExprValue(subProp.value);
                                }
                            } else if (subKey === 'default') {
                                if (subProp.value.type === 'Literal') {
                                    property.defaultValue = subProp.value.value;
                                } else {
                                    property.defaultValue = 'unknown';
                                }
                            }
                        }
                    });
                } else if (prop.value.type === 'Literal') {
                    // 直接赋值的属性
                    property.defaultValue = prop.value.value;
                }
                
                properties.push(property);
            }
        });
    }
    
    return properties;
}

/**
 * 从代码中提取所有cc.Class定义
 * @param {string} code - 代码内容
 * @returns {Array} - cc.Class定义列表
 */
function extractAllCcClasses(code) {
    const classDefs = [];
    
    // 正则匹配cc.Class调用
    const classPattern = /cc\.Class\s*\(\s*\{([\s\S]*?)\}\s*\)/g;
    let match;
    
    while ((match = classPattern.exec(code)) !== null) {
        const classBody = match[1];
        try {
            // 尝试解析类定义
            const classObj = eval(`({${classBody}})`);
            const classDef = {
                type: 'cc_class',
                name: classObj.name || 'UnknownClass',
                extends: classObj.extends || 'cc.Component',
                properties: [],
                methods: []
            };
            
            // 处理属性
            if (classObj.properties) {
                Object.keys(classObj.properties).forEach(propName => {
                    const propValue = classObj.properties[propName];
                    const property = {
                        name: propName,
                        type: 'any',
                        defaultValue: null
                    };
                    
                    if (typeof propValue === 'object') {
                        property.type = propValue.type || 'any';
                        property.defaultValue = propValue.default || null;
                    } else {
                        property.defaultValue = propValue;
                    }
                    
                    classDef.properties.push(property);
                });
            }
            
            // 处理方法
            Object.keys(classObj).forEach(key => {
                const value = classObj[key];
                if (typeof value === 'function' && key !== 'constructor') {
                    classDef.methods.push({
                        name: key,
                        params: [],
                        type: 'function'
                    });
                }
            });
            
            classDefs.push(classDef);
        } catch (e) {
            // 忽略无法解析的类定义
            continue;
        }
    }
    
    return classDefs;
}

/**
 * 解析JavaScript代码，生成中间JSON
 * @param {string} inputPath - 输入文件或目录
 * @param {string} outputPath - 输出JSON文件路径
 */
function parseBundle(inputPath, outputPath) {
    console.log('开始解析JavaScript代码...');
    console.log(`输入: ${inputPath}`);
    console.log(`输出: ${outputPath}`);
    
    let files = [];
    
    // 检查输入是文件还是目录
    if (fs.existsSync(inputPath)) {
        const stats = fs.statSync(inputPath);
        if (stats.isDirectory()) {
            // 处理目录
            files = getFilesFromDirectory(inputPath);
        } else {
            // 处理单个文件
            files = [inputPath];
        }
    } else {
        console.error(`输入路径不存在: ${inputPath}`);
        process.exit(1);
    }
    
    console.log(`找到 ${files.length} 个JavaScript文件`);
    
    // 分析每个文件
    for (const filePath of files) {
        analyzeFile(filePath, outputPath);
    }
    
    console.log('解析完成！');
}

/**
 * 从目录获取所有JavaScript文件
 * @param {string} dirPath - 目录路径
 * @returns {Array} - 文件路径列表
 */
function getFilesFromDirectory(dirPath) {
    let files = [];
    
    function traverseDir(dir) {
        const entries = fs.readdirSync(dir);
        
        for (const entry of entries) {
            const entryPath = path.join(dir, entry);
            const stats = fs.statSync(entryPath);
            
            if (stats.isDirectory()) {
                traverseDir(entryPath);
            } else if (entry.endsWith('.js')) {
                files.push(entryPath);
            }
        }
    }
    
    traverseDir(dirPath);
    return files;
}

/**
 * 分析单个JavaScript文件
 * @param {string} filePath - 文件路径
 * @param {string} outputPath - 输出目录路径
 */
function analyzeFile(filePath, outputPath) {
    try {
        console.log(`分析文件: ${filePath}`);
        
        const content = fs.readFileSync(filePath, 'utf-8');
        
        let modules = [];
        
        // 检查是否是Webpack bundle
        if (isWebpackBundle(content)) {
            console.log(`检测到Webpack bundle文件: ${filePath}`);
            // 解析Webpack bundle
            modules = parseWebpackBundle(content);
        } else {
            // 解析AST
            const ast = parser.parse(content, {
                sourceType: 'script',
                plugins: ['jsx', 'typescript']
            });
            
            // 提取模块信息
            // 先查找所有cc.Class调用
            const classDefinitions = [];
            traverse(ast, {
                CallExpression(path) {
                    const c = path.node.callee;
                    if (
                        c.type === 'MemberExpression' &&
                        c.object.name === 'cc' &&
                        c.property.name === 'Class'
                    ) {
                        const classDef = parseCcClassCall(path.node);
                        if (classDef) {
                            classDefinitions.push(classDef);
                        }
                    }
                }
            });
            
            // 查找所有cc._RF.push调用
            traverse(ast, {
                CallExpression(path) {
                    const callee = path.node.callee;
                    
                    // 检查是否是 cc._RF.push 调用
                    if (
                        callee.type === 'MemberExpression' &&
                        callee.object.type === 'MemberExpression' &&
                        callee.object.object.name === 'cc' &&
                        callee.object.property.name === '_RF' &&
                        callee.property.name === 'push'
                    ) {
                        const args = path.node.arguments;
                        // 获取模块名（第三个参数）
                        const moduleName = args[2]?.value;
                        if (!moduleName) return;
            
                        console.log(`找到模块: ${moduleName}`);
            
                        const mod = {
                            module: moduleName,
                            imports: {},
                            staticProperties: [],
                            classDefinitions: classDefinitions
                        };
            
                        // 查找静态属性
                        traverse(ast, {
                            // 查找 e._xxx = value 形式的静态字段赋值
                            AssignmentExpression(p) {
                                if (
                                    p.node.left.type === 'MemberExpression' &&
                                    p.node.left.object.name === 'e' &&
                                    p.node.left.property.type === 'Identifier'
                                ) {
                                    const propName = p.node.left.property.name;
                                    mod.staticProperties.push(propName);
                                }
                            },
                            
                            // 查找 Object.defineProperty 调用
                            CallExpression(p) {
                                const c = p.node.callee;
                                if (
                                    c.type === 'MemberExpression' &&
                                    c.object.name === 'Object' &&
                                    c.property.name === 'defineProperty'
                                ) {
                                    const obj = p.node.arguments[0];
                                    if (obj && obj.type === 'Identifier' && obj.name === 'e') {
                                        const propName = p.node.arguments[1]?.value;
                                        if (propName) {
                                            mod.staticProperties.push(propName);
                                        }
                                    }
                                }
                            }
                        });
            
                        // 无论是否找到函数父级，都添加模块
                        modules.push(mod);
                        console.log(`模块处理完成: ${moduleName}, 导入数: ${Object.keys(mod.imports).length}, 静态属性数: ${mod.staticProperties.length}, 类定义数: ${mod.classDefinitions.length}`);
                    }
                },
            });
            
            // 如果没有找到cc._RF.push调用，但找到了classDefinitions，创建一个默认模块
            if (modules.length === 0 && classDefinitions.length > 0) {
                console.log('没有找到cc._RF.push调用，创建默认模块');
                const mod = {
                    module: 'default_module',
                    imports: {},
                    staticProperties: [],
                    classDefinitions: classDefinitions
                };
                modules.push(mod);
            }
        }
        
        // 写入JSON文件 - 检查outputPath是文件还是目录
        let jsonOutputPath;
        if (path.extname(outputPath) === '.json') {
            // 如果是JSON文件路径，直接使用
            const outputDir = path.dirname(outputPath);
            fs.ensureDirSync(outputDir);
            jsonOutputPath = outputPath;
        } else {
            // 如果是目录路径，生成带文件名的JSON路径
            fs.ensureDirSync(outputPath);
            const baseName = path.basename(filePath);
            jsonOutputPath = path.join(outputPath, `${baseName}.json`);
        }
        
        fs.writeJsonSync(jsonOutputPath, modules, { spaces: 2 });
        
        console.log(`解析完成: ${filePath}`);
        console.log(`生成JSON: ${jsonOutputPath}`);
        console.log(`解析模块数: ${modules.length}`);
        
        return {
            success: true,
            modules: modules
        };
    } catch (error) {
        console.error(`分析失败: ${filePath}`, error.message);
        return {
            success: false,
            error: error.message,
            filePath: filePath
        };
    }
}

/**
 * 解析cc.Class调用
 * @param {Object} node - CallExpression节点
 * @returns {Object} - 类定义
 */
function parseCcClassCall(node) {
    if (!node.arguments || node.arguments.length === 0) {
        return null;
    }
    
    const classObj = node.arguments[0];
    if (classObj.type !== 'ObjectExpression') {
        return null;
    }
    
    const result = {
        type: 'cc_class',
        name: null,
        extends: 'cc.Component',
        properties: [],
        methods: []
    };
    
    // 提取类属性
    classObj.properties.forEach(prop => {
        if (prop.type !== 'ObjectProperty') {
            return;
        }
        
        // 获取属性名
        let propKey;
        if (prop.key.type === 'Identifier') {
            propKey = prop.key.name;
        } else if (prop.key.type === 'StringLiteral' || prop.key.type === 'NumericLiteral') {
            propKey = prop.key.value;
        } else {
            return;
        }
        
        const propValue = prop.value;
        
        switch (propKey) {
            case 'name':
                if (propValue.type === 'StringLiteral') {
                    result.name = propValue.value;
                } else {
                    result.name = extractExpressionValue(propValue);
                }
                break;
            
            case 'extends':
                result.extends = extractExpressionValue(propValue);
                break;
            
            case 'properties':
                result.properties = parseProperties(propValue);
                break;
            
            default:
                // 检查是否是方法
                if (propValue.type === 'FunctionExpression' || propValue.type === 'ArrowFunctionExpression') {
                    result.methods.push({
                        name: propKey,
                        params: extractFunctionParams(propValue),
                        type: propValue.type === 'ArrowFunctionExpression' ? 'arrow' : 'function'
                    });
                }
        }
    });
    
    // 如果没有提取到类名，使用默认名称
    if (!result.name) {
        result.name = 'UnknownClass';
    }
    
    return result;
}

/**
 * 提取表达式值
 * @param {Object} expr - 表达式节点
 * @returns {string} - 表达式值
 */
function extractExpressionValue(expr) {
    if (expr.type === 'Identifier') {
        return expr.name;
    } else if (expr.type === 'MemberExpression') {
        const parts = [];
        let current = expr;
        while (current) {
            if (current.property && current.property.name) {
                parts.unshift(current.property.name);
            }
            if (current.object.type === 'Identifier') {
                parts.unshift(current.object.name);
                break;
            } else if (current.object.type === 'MemberExpression') {
                current = current.object;
            } else {
                break;
            }
        }
        return parts.join('.');
    } else if (expr.type === 'StringLiteral' || expr.type === 'NumericLiteral') {
        return expr.value;
    }
    return 'unknown';
}

/**
 * 解析属性定义
 * @param {Object} propNode - 属性节点
 * @returns {Array} - 属性列表
 */
function parseProperties(propNode) {
    if (propNode.type !== 'ObjectExpression') {
        return [];
    }
    
    const properties = [];
    
    propNode.properties.forEach(prop => {
        if (prop.type !== 'ObjectProperty') return;
        
        const propName = prop.key.name || prop.key.value;
        const propValue = prop.value;
        
        const property = {
            name: propName,
            type: 'any',
            defaultValue: null
        };
        
        // 解析属性定义对象
        if (propValue.type === 'ObjectExpression') {
            propValue.properties.forEach(subProp => {
                if (subProp.type !== 'ObjectProperty') return;
                
                const subPropKey = subProp.key.name;
                const subPropValue = subProp.value;
                
                switch (subPropKey) {
                    case 'type':
                        property.type = extractExpressionValue(subPropValue);
                        break;
                    case 'default':
                        property.defaultValue = extractExpressionValue(subPropValue);
                        break;
                }
            });
        } else {
            // 直接赋值的属性
            property.defaultValue = extractExpressionValue(propValue);
        }
        
        properties.push(property);
    });
    
    return properties;
}

/**
 * 提取函数参数
 * @param {Object} funcNode - 函数节点
 * @returns {Array} - 参数列表
 */
function extractFunctionParams(funcNode) {
    return funcNode.params.map(param => param.name || 'arg');
}

/**
 * 美化JavaScript代码
 * @param {string} code - 原始代码
 * @returns {string} - 美化后的代码
 */
function prettifyCode(code) {
    try {
        return prettier.format(code, {
            parser: 'babel',
            semi: true,
            singleQuote: true,
            tabWidth: 2
        });
    } catch (error) {
        console.warn('Prettier美化失败，使用原始代码');
        return code;
    }
}

/**
 * 命令行入口
 */
function main() {
    const args = process.argv.slice(2);
    
    if (args.length !== 2) {
        console.error('用法: node parse_bundle.js <input> <output_dir>');
        process.exit(1);
    }
    
    const [inputPath, outputPath] = args;
    parseBundle(inputPath, outputPath);
}

if (require.main === module) {
    main();
}

module.exports = {
    parseBundle,
    analyzeFile
};