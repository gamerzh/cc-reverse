/**
 * parse_bundle.js
 * Node.js分析器 - 负责理解代码，生成中间JSON
 */

const fs = require('fs-extra');
const path = require('path');
const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;
const prettier = require('prettier');

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
        
        // 解析AST
        const ast = parser.parse(content, {
            sourceType: 'script'
        });
        
        // 提取模块信息
        const modules = [];
        
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