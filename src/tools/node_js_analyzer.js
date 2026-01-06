/**
 * Node.js代码分析器
 * 使用Babel/Esprima分析JavaScript代码，生成中间JSON格式
 * 
 * 架构设计：
 * [Node.js] -> 分析代码 -> 生成中间JSON
 *      ↓
 * [Python] -> 读取JSON -> 生成最终代码
 */

const fs = require('fs');
const path = require('path');
const esprima = require('esprima');
const babel = require('@babel/core');
const prettier = require('prettier');

/**
 * 分析单个JavaScript文件
 * @param {string} filePath - 文件路径
 * @returns {Object} - 分析结果
 */
function analyzeFile(filePath) {
    try {
        console.log(`分析文件: ${filePath}`);
        
        const content = fs.readFileSync(filePath, 'utf-8');
        
        // 1. 使用Esprima解析AST
        const ast = esprima.parseScript(content, {
            range: true,
            loc: true,
            tolerant: true
        });
        
        // 2. 提取模块信息
        const analysisResult = {
            filePath: filePath,
            fileName: path.basename(filePath),
            moduleName: extractModuleName(content, ast),
            dependencies: extractDependencies(content, ast),
            classDefinitions: extractClassDefinitions(ast),
            staticFields: extractStaticFields(ast),
            methods: extractMethods(ast),
            originalContent: content
        };
        
        // 3. 使用Prettier美化原始代码（可选）
        const prettifiedCode = prettier.format(content, {
            parser: 'babel',
            semi: true,
            singleQuote: true,
            tabWidth: 2
        });
        analysisResult.prettifiedContent = prettifiedCode;
        
        return {
            success: true,
            data: analysisResult
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
 * 提取模块名（从cc._RF.push中）
 * @param {string} content - 文件内容
 * @param {Object} ast - AST对象
 * @returns {string|null} - 模块名
 */
function extractModuleName(content, ast) {
    // 使用正则表达式快速提取
    const pushMatch = content.match(/cc\._RF\.push\([^,]+,\s*["']([^"']+)["']/);
    if (pushMatch) {
        return pushMatch[1];
    }
    
    // 从文件名推断
    return path.basename(filePath, '.js');
}

/**
 * 提取依赖关系
 * @param {string} content - 文件内容
 * @param {Object} ast - AST对象
 * @returns {Array} - 依赖列表
 */
function extractDependencies(content, ast) {
    const dependencies = [];
    
    // 正则表达式提取依赖
    const requireRegex = /require\(["']([^"']+)["']\)/g;
    let match;
    while ((match = requireRegex.exec(content)) !== null) {
        dependencies.push({
            path: match[1],
            name: path.basename(match[1], '.js')
        });
    }
    
    return dependencies;
}

/**
 * 提取类定义
 * @param {Object} ast - AST对象
 * @returns {Array} - 类定义列表
 */
function extractClassDefinitions(ast) {
    const classes = [];
    
    // 遍历AST查找类定义
    function traverse(node) {
        if (!node) return;
        
        // 处理cc.Class调用
        if (node.type === 'CallExpression' && 
            node.callee.type === 'MemberExpression' &&
            node.callee.object.type === 'Identifier' &&
            node.callee.object.name === 'cc' &&
            node.callee.property.type === 'Identifier' &&
            node.callee.property.name === 'Class') {
            
            const classObj = parseCcClassCall(node);
            if (classObj) {
                classes.push(classObj);
            }
        }
        
        // 处理ES6类定义
        if (node.type === 'ClassDeclaration') {
            classes.push(parseEs6Class(node));
        }
        
        // 递归遍历
        for (const key in node) {
            if (typeof node[key] === 'object' && node[key] !== null) {
                if (Array.isArray(node[key])) {
                    node[key].forEach(traverse);
                } else {
                    traverse(node[key]);
                }
            }
        }
    }
    
    traverse(ast);
    return classes;
}

/**
 * 解析cc.Class调用
 * @param {Object} node - CallExpression节点
 * @returns {Object|null} - 类定义
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
        methods: [],
        statics: []
    };
    
    // 提取类属性
    classObj.properties.forEach(prop => {
        if (prop.type !== 'Property') return;
        
        const propKey = prop.key.name || prop.key.value;
        const propValue = prop.value;
        
        switch (propKey) {
            case 'name':
                if (propValue.type === 'Literal') {
                    result.name = propValue.value;
                }
                break;
                
            case 'extends':
                result.extends = extractExpressionValue(propValue);
                break;
                
            case 'properties':
                result.properties = parseProperties(propValue);
                break;
                
            case 'statics':
                result.statics = parseProperties(propValue);
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
    
    return result;
}

/**
 * 解析ES6类
 * @param {Object} node - ClassDeclaration节点
 * @returns {Object} - 类定义
 */
function parseEs6Class(node) {
    return {
        type: 'es6_class',
        name: node.id.name,
        extends: node.superClass ? extractExpressionValue(node.superClass) : null,
        properties: [],
        methods: []
    };
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
    } else if (expr.type === 'Literal') {
        return expr.value;
    } else if (expr.type === 'ObjectExpression') {
        // 处理对象表达式
        return JSON.stringify(expr.properties.map(prop => ({
            [prop.key.name]: extractExpressionValue(prop.value)
        })));
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
        if (prop.type !== 'Property') return;
        
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
                if (subProp.type !== 'Property') return;
                
                const subPropKey = subProp.key.name;
                const subPropValue = subProp.value;
                
                switch (subPropKey) {
                    case 'type':
                        property.type = extractExpressionValue(subPropValue);
                        break;
                        
                    case 'default':
                        property.defaultValue = extractExpressionValue(subPropValue);
                        break;
                        
                    case 'visible':
                        property.visible = subPropValue.value;
                        break;
                        
                    case 'serializable':
                        property.serializable = subPropValue.value;
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
 * 提取静态字段
 * @param {Object} ast - AST对象
 * @returns {Array} - 静态字段列表
 */
function extractStaticFields(ast) {
    const staticFields = [];
    
    // 遍历AST查找静态字段赋值
    function traverse(node) {
        if (!node) return;
        
        // 查找 e._xxx = value 形式的静态字段
        if (node.type === 'AssignmentExpression' &&
            node.left.type === 'MemberExpression' &&
            node.left.object.type === 'Identifier' &&
            node.left.object.name === 'e' &&
            node.left.property.type === 'Identifier' &&
            node.left.property.name.startsWith('_')) {
            
            staticFields.push({
                name: node.left.property.name,
                value: extractExpressionValue(node.right),
                type: inferType(node.right)
            });
        }
        
        // 递归遍历
        for (const key in node) {
            if (typeof node[key] === 'object' && node[key] !== null) {
                if (Array.isArray(node[key])) {
                    node[key].forEach(traverse);
                } else {
                    traverse(node[key]);
                }
            }
        }
    }
    
    traverse(ast);
    return staticFields;
}

/**
 * 推断值类型
 * @param {Object} expr - 表达式节点
 * @returns {string} - 推断的类型
 */
function inferType(expr) {
    switch (expr.type) {
        case 'Literal':
            return typeof expr.value;
        case 'ObjectExpression':
            return 'object';
        case 'ArrayExpression':
            return 'array';
        case 'CallExpression':
            return 'function';
        default:
            return 'any';
    }
}

/**
 * 提取方法定义
 * @param {Object} ast - AST对象
 * @returns {Array} - 方法列表
 */
function extractMethods(ast) {
    const methods = [];
    
    // 遍历AST查找方法
    function traverse(node) {
        if (!node) return;
        
        // 查找函数定义
        if (node.type === 'FunctionDeclaration') {
            methods.push({
                name: node.id.name,
                params: extractFunctionParams(node),
                type: 'function'
            });
        }
        
        // 递归遍历
        for (const key in node) {
            if (typeof node[key] === 'object' && node[key] !== null) {
                if (Array.isArray(node[key])) {
                    node[key].forEach(traverse);
                } else {
                    traverse(node[key]);
                }
            }
        }
    }
    
    traverse(ast);
    return methods;
}

/**
 * 批量分析目录中的JavaScript文件
 * @param {string} dirPath - 目录路径
 * @returns {Array} - 分析结果列表
 */
function analyzeDirectory(dirPath) {
    const results = [];
    
    function processDir(currentDir) {
        const files = fs.readdirSync(currentDir);
        
        files.forEach(file => {
            const filePath = path.join(currentDir, file);
            const stats = fs.statSync(filePath);
            
            if (stats.isDirectory()) {
                processDir(filePath);
            } else if (path.extname(file) === '.js') {
                const result = analyzeFile(filePath);
                results.push(result);
            }
        });
    }
    
    processDir(dirPath);
    return results;
}

/**
 * 主函数
 * @param {string} inputPath - 输入文件或目录
 * @param {string} outputPath - 输出JSON文件路径
 */
function main(inputPath, outputPath) {
    console.log('开始代码分析...');
    console.log(`输入: ${inputPath}`);
    console.log(`输出: ${outputPath}`);
    
    const stats = fs.statSync(inputPath);
    let results;
    
    if (stats.isDirectory()) {
        results = analyzeDirectory(inputPath);
    } else {
        results = [analyzeFile(inputPath)];
    }
    
    // 生成中间JSON文件
    const outputData = {
        generatedAt: new Date().toISOString(),
        totalFiles: results.length,
        successful: results.filter(r => r.success).length,
        failed: results.filter(r => !r.success).length,
        results: results
    };
    
    // 写入输出文件
    fs.writeFileSync(outputPath, JSON.stringify(outputData, null, 2), 'utf-8');
    
    console.log('分析完成！');
    console.log(`总文件数: ${results.length}`);
    console.log(`成功: ${outputData.successful}`);
    console.log(`失败: ${outputData.failed}`);
    console.log(`结果文件: ${outputPath}`);
}

// 命令行参数处理
if (require.main === module) {
    const args = process.argv.slice(2);
    
    if (args.length !== 2) {
        console.error('用法: node node_js_analyzer.js <输入文件/目录> <输出JSON文件>');
        process.exit(1);
    }
    
    const [inputPath, outputPath] = args;
    main(inputPath, outputPath);
}

// 导出模块（用于其他Node.js脚本调用）
module.exports = {
    analyzeFile,
    analyzeDirectory,
    extractModuleName,
    extractDependencies,
    extractClassDefinitions
};