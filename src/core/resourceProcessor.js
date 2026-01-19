/*
 * @Date: 2025-06-07 10:06:12
 * @Description: Cocos Creator 资源处理工具
 */
const fs = require("fs");
const path = require("path");
const { promisify } = require('util');
const { uuidUtils } = require('../utils/uuidUtils');
const { fileManager } = require('../utils/fileManager');
const { logger } = require('../utils/logger');
const { converters } = require('./converters');
const { serializationParser } = require('./serializationParser');

// 将 fs 方法转换为 Promise
const readdir = promisify(fs.readdir);
const stat = promisify(fs.stat);
const readFile = promisify(fs.readFile);

/**
 * 资源处理器模块
 */
const resourceProcessor = {
    // 数据存储
    fileList: [],
    fileMap: new Map(),
    cacheReadList: [],
    cacheWriteList: [],
    nodeData: {},
    
    // 资源映射
    sceneAssets: [],
    spriteFrames: {},
    audio: [],
    animation: [],

    // 2.4.x bundle config 映射（仅靠编译产物也可恢复可读名称）
    uuidPathMap: new Map(),
    importHashToUuid: new Map(),
    importHashToPath: new Map(),
    
    /**
     * 处理资源文件
     * @returns {Promise<void>}
     */
    async processResources() {
        try {
            this.resetState();
            
            // 读取资源文件
            await this.readFiles(global.paths.res, true);
            
            // 转换为输出文件
            await this.convertToOutputFiles();
            
            logger.info('资源处理完成');
        } catch (err) {
            logger.error('处理资源文件时出错:', err);
            throw err;
        }
    },
    
    /**
     * 重置处理器状态
     */
    resetState() {
        this.fileList = [];
        this.fileMap = new Map();
        this.cacheReadList = [];
        this.cacheWriteList = [];
        this.nodeData = {};
        this.sceneAssets = [];
        this.spriteFrames = {};
        this.audio = [];
        this.animation = [];

        this.uuidPathMap = new Map();
        this.importHashToUuid = new Map();
        this.importHashToPath = new Map();
    },

    /**
     * 从编译产物的 bundle config.*.json 中建立 uuid -> 原始路径 的映射。
     * 说明：Cocos Creator 2.4.x 的 bundle config 通常包含 uuids + paths 表，可用于恢复资源的可读路径。
     */
    async buildUuidPathMapFromBundleConfigs() {
        try {
            const map = new Map();
            const importHashToUuid = new Map();
            const importHashToPath = new Map(); // 新增：import hash -> asset name
            for (const filePath of this.fileList) {
                const ext = path.extname(filePath).toLowerCase();
                if (ext !== '.json') continue;
                const fileName = path.basename(filePath);

                // 常见命名：config.<hash>.json 或 config.json
                if (!/^config(\.[a-f0-9]+)?\.json$/i.test(fileName)) continue;

                let json;
                try {
                    const content = await readFile(filePath, 'utf-8');
                    json = JSON.parse(content);
                } catch {
                    continue;
                }

                if (!json || !json.uuids || !json.paths) continue;
                const bundleName = this.extractBundleName(filePath) || 'common';

                const uuids = Array.isArray(json.uuids) ? json.uuids : [];
                const decode = (id) => {
                    if (typeof id !== 'string') return '';
                    return (id.length === 22) ? (uuidUtils.decodeUuid(id) || id) : id;
                };

                const record = (uuid, p) => {
                    if (!uuid || typeof p !== 'string' || !p) return;
                    // 只记录一次；若多 bundle 重复，保留先遇到的
                    if (!map.has(uuid)) {
                        map.set(uuid, { path: p, bundle: bundleName });
                    }
                };

                const paths = json.paths;
                const pathsByIndex = new Map(); // 建立 index -> name 的映射
                
                if (Array.isArray(paths)) {
                    for (let i = 0; i < paths.length; i++) {
                        const uuid = decode(uuids[i]);
                        const item = paths[i];
                        const p = Array.isArray(item) ? item[0] : item;
                        record(uuid, p);
                        pathsByIndex.set(i, p);
                    }
                } else if (paths && typeof paths === 'object') {
                    for (const k of Object.keys(paths)) {
                        const idx = Number(k);
                        if (!Number.isFinite(idx)) continue;
                        const uuid = decode(uuids[idx]);
                        const item = paths[k];
                        const p = Array.isArray(item) ? item[0] : item;
                        record(uuid, p);
                        pathsByIndex.set(idx, p);
                    }
                }

                // scenes 表有时单独存在
                if (json.scenes && typeof json.scenes === 'object') {
                    for (const k of Object.keys(json.scenes)) {
                        const idx = Number(k);
                        if (!Number.isFinite(idx)) continue;
                        const uuid = decode(uuids[idx]);
                        const p = json.scenes[k];
                        record(uuid, p);
                        pathsByIndex.set(idx, p);
                    }
                }

                // versions.import: [idx, md5, idx, md5, ...] 或 [[idx, md5], ...]
                // 用于从 md5 文件名反查 uuid
                const vImport = json.versions && json.versions.import;
                const vNative = json.versions && json.versions.native;
                const nativeByIdx = new Map();

                const addNative = (idx, hash) => {
                    const i = Number(idx);
                    if (!Number.isFinite(i)) return;
                    if (typeof hash !== 'string' || !hash) return;
                    nativeByIdx.set(i, hash);
                };

                if (Array.isArray(vNative)) {
                    if (vNative.length > 0 && Array.isArray(vNative[0])) {
                        for (const pair of vNative) {
                            if (Array.isArray(pair) && pair.length >= 2) {
                                addNative(pair[0], pair[1]);
                            }
                        }
                    } else {
                        for (let i = 0; i + 1 < vNative.length; i += 2) {
                            addNative(vNative[i], vNative[i + 1]);
                        }
                    }
                }

                const addImportMap = (idx, hash) => {
                    const i = Number(idx);
                    if (!Number.isFinite(i)) return;
                    if (typeof hash !== 'string' || !hash) return;
                    const uuid = decode(uuids[i]);
                    if (!uuid) return;
                    if (!importHashToUuid.has(hash)) {
                        importHashToUuid.set(hash, { uuid, bundle: bundleName });
                    }

                    // 同时记录 importHash -> path
                    const p = pathsByIndex.get(i);
                    if (p && !importHashToPath.has(hash)) {
                        importHashToPath.set(hash, { path: p, bundle: bundleName });
                    }

                    // 有些构建的 import 文件名会拼接 native hash：<import>.<native>
                    const n = nativeByIdx.get(i);
                    if (n && !importHashToUuid.has(`${hash}.${n}`)) {
                        importHashToUuid.set(`${hash}.${n}`, { uuid, bundle: bundleName });
                    }
                    if (n && p && !importHashToPath.has(`${hash}.${n}`)) {
                        importHashToPath.set(`${hash}.${n}`, { path: p, bundle: bundleName });
                    }
                };

                if (Array.isArray(vImport)) {
                    if (vImport.length > 0 && Array.isArray(vImport[0])) {
                        for (const pair of vImport) {
                            if (Array.isArray(pair) && pair.length >= 2) {
                                addImportMap(pair[0], pair[1]);
                            }
                        }
                    } else {
                        for (let i = 0; i + 1 < vImport.length; i += 2) {
                            addImportMap(vImport[i], vImport[i + 1]);
                        }
                    }
                }

                // 处理 packs 字段：packs[importHash] = [assetIndex1, assetIndex2, ...]
                // 这样可以通过 import 文件名直接查找到该文件包含的所有资源名称
                if (json.packs && typeof json.packs === 'object') {
                    for (const importHash of Object.keys(json.packs)) {
                        const indices = json.packs[importHash];
                        if (!Array.isArray(indices)) continue;
                        
                        // 为这个 import 文件建立所包含的所有资源名称列表
                        const assetNames = [];
                        const typesArray = Array.isArray(json.types) ? json.types : [];
                        
                        // 首先查找 cc.Prefab 类型的资源
                        let prefabName = '';
                        let firstAssetPath = '';
                        
                        for (const idx of indices) {
                            const i = Number(idx);
                            if (!Number.isFinite(i)) continue;
                            const p = pathsByIndex.get(i);
                            if (!p) continue;
                            
                            if (!firstAssetPath) {
                                firstAssetPath = p; // 记录第一个资源作为备选
                            }
                            
                            // 检查这个资源的类型
                            const item = Array.isArray(paths[i]) ? paths[i] : paths[String(i)];
                            if (Array.isArray(item)) {
                                const typeIdx = item[1]; // paths[i] = [name, typeIndex, ...] 格式
                                if (typeof typeIdx === 'number' && typeIdx < typesArray.length) {
                                    const typeStr = typesArray[typeIdx];
                                    if (typeStr === 'cc.Prefab' && !prefabName) {
                                        prefabName = p; // 找到了 prefab，记录其名称
                                    }
                                }
                            }
                            
                            assetNames.push(p);
                            
                            // 也可以为 importHash.nativeHash 格式建立映射
                            const n = nativeByIdx.get(i);
                            if (n) {
                                // importHash.nativeHash 对应的资源名
                                const key = `${importHash}.${n}`;
                                if (!importHashToPath.has(key)) {
                                    importHashToPath.set(key, { path: p, bundle: bundleName });
                                }
                            }
                        }
                        
                        // 为 importHash 建立完整的资源名列表，优先使用 prefab，其次使用第一个资源
                        if (assetNames.length > 0 && !importHashToPath.has(importHash)) {
                            importHashToPath.set(importHash, { 
                                paths: assetNames,
                                path: prefabName || firstAssetPath, // 主资源优先为 prefab，其次为第一个
                                bundle: bundleName 
                            });
                        }
                    }
                }
            }

            this.uuidPathMap = map;
            global.uuidPathMap = map;
            this.importHashToUuid = importHashToUuid;
            global.importHashToUuid = importHashToUuid;
            this.importHashToPath = importHashToPath;
            global.importHashToPath = importHashToPath;
            if (global.verbose) {
                logger.info(`[命名映射] 从 bundle config 建立 uuid->path 映射数量: ${map.size}`);
                logger.info(`[命名映射] 从 bundle config 建立 importHash->uuid 映射数量: ${importHashToUuid.size}`);
                logger.info(`[命名映射] 从 bundle config 建立 importHash->path 映射数量: ${importHashToPath.size}`);
            }
        } catch (err) {
            logger.warn('从 bundle config 构建 uuid->path 映射失败:', err);
            this.uuidPathMap = new Map();
            global.uuidPathMap = this.uuidPathMap;
            this.importHashToUuid = new Map();
            global.importHashToUuid = this.importHashToUuid;
            this.importHashToPath = new Map();
            global.importHashToPath = this.importHashToPath;
        }
    },

    /**
     * 从所有bundle的config文件的paths字段中构建完整的目录结构
     * 这个函数完全依赖编译产物，不需要原项目
     * 关键：按bundle记录路径，保持相对关系
     * @returns {Promise<void>}
     */
    async buildDirectoryStructureFromBundleConfigs() {
        const bundlePathsMap = new Map(); // bundle名称 -> {paths: [], directories: []}
        const allAssetPaths = new Set();
        
        try {
            for (const filePath of this.fileList) {
                const ext = path.extname(filePath).toLowerCase();
                if (ext !== '.json') continue;
                const fileName = path.basename(filePath);

                // 只处理 config.<hash>.json 或 config.json
                if (!/^config(\.[a-f0-9]+)?\.json$/i.test(fileName)) continue;

                let json;
                try {
                    const content = await readFile(filePath, 'utf-8');
                    json = JSON.parse(content);
                } catch {
                    continue;
                }

                if (!json || !json.paths) continue;

                // 提取bundle名称
                const bundleName = this.extractBundleName(filePath) || 'common';
                if (!bundlePathsMap.has(bundleName)) {
                    bundlePathsMap.set(bundleName, { paths: [], directories: new Set() });
                }

                const bundleInfo = bundlePathsMap.get(bundleName);
                const paths = json.paths;
                const pathsList = [];
                
                // 提取所有路径
                if (Array.isArray(paths)) {
                    pathsList.push(...paths.map(p => Array.isArray(p) ? p[0] : p));
                } else if (paths && typeof paths === 'object') {
                    for (const k of Object.keys(paths)) {
                        const item = paths[k];
                        const p = Array.isArray(item) ? item[0] : item;
                        if (typeof p === 'string') pathsList.push(p);
                    }
                }

                // scenes 字段
                if (json.scenes && typeof json.scenes === 'object') {
                    for (const p of Object.values(json.scenes)) {
                        if (typeof p === 'string') pathsList.push(p);
                    }
                }

                // 为这个bundle记录所有路径和目录
                for (const assetPath of pathsList) {
                    if (!assetPath || typeof assetPath !== 'string') continue;
                    
                    bundleInfo.paths.push(assetPath);
                    allAssetPaths.add(assetPath);
                    
                    // 提取该路径的所有中间目录
                    const parts = assetPath.split('/');
                    for (let i = 0; i < parts.length - 1; i++) {
                        const dirPath = parts.slice(0, i + 1).join('/');
                        bundleInfo.directories.add(dirPath);
                    }
                }
            }

            // 保存到全局状态供后续使用
            global.bundlePathsMap = bundlePathsMap;
            global.bundleAssetPaths = allAssetPaths;
            
            if (global.verbose) {
                let totalDirs = 0;
                for (const [bundle, info] of bundlePathsMap) {
                    totalDirs += info.directories.size;
                    logger.info(`[目录结构] Bundle '${bundle}': ${info.directories.size} 个目录, ${info.paths.length} 个资源`);
                }
                logger.info(`[目录结构] 总计: ${totalDirs} 个目录, ${allAssetPaths.size} 个资源路径`);
            }
        } catch (err) {
            logger.warn('从 bundle config 构建目录结构失败:', err);
            global.bundlePathsMap = new Map();
            global.bundleAssetPaths = new Set();
        }
    },
    
    /**
     * 递归读取目录下所有文件
     * @param {string} filePath 文件路径
     * @param {boolean} first 是否为首次调用
     * @returns {Promise<void>}
     */
    async readFiles(filePath, first) {
        try {
            const content = await readdir(filePath);
            
            for (let file of content) {
                const fullPath = path.join(filePath, file);
                const status = await stat(fullPath);
                
                if (status.isFile()) {
                    this.fileList.push(fullPath);
                    this.fileMap.set(path.basename(fullPath.split('.')[0]), fullPath);
                } else {
                    await this.readFiles(fullPath, false);
                }
            }
            
            if (first) {
                await this.processSubpackages();
                await this.processJsonFiles();
            }
        } catch (err) {
            logger.error(`读取目录 ${filePath} 时出错:`, err);
            throw err;
        }
    },
    
    /**
     * 处理子包
     * @returns {Promise<void>}
     */
    async processSubpackages() {
        if (global.settings && !this.isEmptyObject(global.settings["subpackages"])) {
            const subpackagesPath = path.dirname(global.paths.res) + '/subpackages';
            
            if (fs.existsSync(subpackagesPath)) {
                await this.readFiles(subpackagesPath, false);
                logger.debug(`处理子包: ${subpackagesPath}`);
            } else {
                logger.warn(`子包路径不存在: ${subpackagesPath}`);
            }
        }
    },
    
    /**
     * 处理 JSON 文件
     * @returns {Promise<void>}
     */
    async processJsonFiles() {
        for (let currPath of this.fileList) {
            if (path.extname(currPath) === '.json') {
                try {
                    const currFile = await readFile(currPath);
                    const fileName = path.basename(currPath);
                    let key = fileName.split('.')[0];
                    
                    // 如果是 import 文件，尝试从 config packs 映射中推导导出名
                    let importHash = null;
                    const isImportFile = currPath.includes(path.sep + 'import' + path.sep);
                    if (isImportFile && global.importHashToPath) {
                        // import 文件名格式如 "0b55cf59e.a065f.json" 或 "0adea70c0.json"
                        // 提取 import hash（第一个点之前的部分，可能也包含后续的 native hash）
                        const match = fileName.match(/^([a-f0-9]+(?:\.[a-f0-9]+)?)\./i);
                        if (match) {
                            importHash = match[1];
                            const derivedName = serializationParser.deriveNameFromImportHash(importHash);
                            if (derivedName) {
                                if (global.verbose) {
                                    logger.debug(`[命名] 从 import hash ${importHash} 推导名称: ${derivedName}`);
                                }
                                key = derivedName;
                            }
                        }
                    }
                    
                    const data = JSON.parse(currFile);
                    this.nodeData = data;
                    await this.processData(key, data, { importHash, filePath: currPath });
                } catch (err) {
                    logger.error(`处理 JSON 文件 ${currPath} 时出错:`, err);
                }
            }
        }
    },
    
    /**
     * 检查对象是否为空
     * @param {Object} obj 要检查的对象
     * @returns {boolean} 如果对象为空返回 true，否则返回 false
     */
    isEmptyObject(obj) {
        for (let key in obj) {
            return false;
        }
        return true;
    },
    
    /**
     * 处理数据
     * @param {string} key 键名
     * @param {Object} data 要处理的数据
     * @param {Object} options 选项，包含 importHash、filePath 等
     */
    async processData(key, data, options = {}) {
        if (!global.settings || this.isEmptyObject(global.settings)) {
            logger.warn('全局设置为空，跳过数据处理');
            return;
        }
        
        const processedData = await this.revealData(data);
        this.writeProcessedData(processedData, key, options);
    },
    
    /**
     * 解析数据对象
     * @param {Object} jsonObject 要解析的 JSON 对象
     * @returns {Promise<Object>} 解析后的对象
     */
    async revealData(jsonObject) {
        // 这里可以添加数据解析逻辑
        return jsonObject;
    },
    
    /**
     * 写入处理后的数据
     * @param {Object} data 处理后的数据
     * @param {string} key 键名
     * @param {Object} options 选项，包含 importHash、filePath 等
     */
    writeProcessedData(data, key, options = {}) {
        if (data === null || data === undefined) {
            return;
        }
        
        if (typeof data === "object" && data["__type__"]) {
            this.processTypeData(data, key);
        } else {
            for (let i in data) {
                if (data[i] === null || data[i] === undefined) {
                    continue;
                }
                
                const type = data[i]['__type__'];
                if (Array.isArray(data[i])) {
                    this.writeProcessedData(data[i], key, options);
                } else if (type) {
                    this.processTypeObject(type, data, i, key);
                }
            }
        }
    },
    
    /**
     * 处理特定类型的数据
     * @param {Object} data 数据对象
     * @param {string} key 键名
     */
    processTypeData(data, key) {
        const type = data["__type__"];
        
        if (type) {
            if (type === "cc.AudioClip") {
                this.processAudioClip(data, key);
            } else if (type === "cc.TextAsset") {
                this.processTextAsset(data, key);
            } else if (type === "cc.AnimationClip") {
                this.processAnimationClip(data, key);
            }
        }
    },
    
    /**
     * 处理特定类型的对象
     * @param {string} type 对象类型
     * @param {Object} data 数据对象
     * @param {string} index 索引
     * @param {string} key 键名
     */
    processTypeObject(type, data, index, key) {
        if (type === 'cc.SceneAsset') {
            this.processSceneAsset(data, index, key);
        } else if (type === 'cc.SpriteFrame') {
            this.processSpriteFrame(data, index, key);
        }
        // 其他类型的处理可以在这里添加
    },
    
    /**
     * 处理音频资源
     * @param {Object} data 音频数据
     * @param {string} key 键名
     */
    processAudioClip(data, key) {
        const name = data["_name"] + data["_native"];
        const _mkdir = "Audio";
        const uuid = key;
        const metaData = {
            "ver": "1.2.7",
            "uuid": uuid,
            "optimizationPolicy": "AUTO",
            "asyncLoadAssets": false,
            "readonly": false,
            "subMetas": {}
        };
        
        if (this.fileMap.has(uuid)) {
            let writePath = name;
            let currPath = this.fileMap.get(uuid);
            
            this.cacheReadList.push(currPath);
            this.cacheWriteList.push(path.join(global.paths.output, 'assets', _mkdir, writePath));
            this.fileMap.delete(uuid);
        }
        
        fileManager.writeFile(_mkdir, name + ".meta", metaData);
        this.audio.push(data);
    },
    
    /**
     * 处理文本资源
     * @param {Object} data 文本数据
     * @param {string} key 键名
     */
    processTextAsset(data, key) {
        const name = data['_name'] + ".json";
        const uuid = key;
        const _mkdir = "resource";
        const metaData = {
            "ver": "1.2.7",
            "uuid": uuid,
            "subMetas": {}
        };
        
        fileManager.writeFile(_mkdir, name, data);
        fileManager.writeFile(_mkdir, name + ".meta", metaData);
    },
    
    /**
     * 处理动画资源
     * @param {Object} data 动画数据
     * @param {string} key 键名
     */
    processAnimationClip(data, key) {
        const name = data["_name"];
        const _mkdir = "Animation";
        const filename = name + ".anim";
        
        fileManager.writeFile(_mkdir, filename, data);
        this.animation.push(data);
        
        const uuid = key;
        const metaData = {
            "ver": "1.2.7",
            "uuid": uuid,
            "optimizationPolicy": "AUTO",
            "asyncLoadAssets": false,
            "readonly": false,
            "subMetas": {}
        };
        
        fileManager.writeFile(_mkdir, filename + ".meta", metaData);
    },
    
    /**
     * 处理场景资源
     * @param {Object} data 场景数据
     * @param {string} index 索引
     * @param {string} key 键名
     */
    processSceneAsset(data, index, key) {
        const filename = data[0]['_name'] + '.fire';
        const _mkdir = 'Scene';
        
        this.sceneAssets.push(JSON.stringify(data));
        fileManager.writeFile(_mkdir, filename, data);
        
        for (let j in this.nodeData) {
            if (Array.isArray(this.nodeData[j])) {
                if (this.nodeData[j][0]["_name"] == data[0]["_name"]) {
                    const uuid = uuidUtils.decodeUuid(this.createLibrary(j, key));
                    const metaData = {
                        "ver": "1.2.7",
                        "uuid": uuid,
                        "optimizationPolicy": "AUTO",
                        "asyncLoadAssets": false,
                        "readonly": false,
                        "subMetas": {}
                    };
                    fileManager.writeFile(_mkdir, filename + ".meta", metaData);
                }
            }
        }
    },
    
    /**
     * 处理精灵帧资源
     * @param {Object} data 精灵帧数据
     * @param {string} index 索引
     * @param {string} key 键名
     */
    processSpriteFrame(data, index, key) {
        // 精灵帧处理逻辑
        this.spriteFrames[key] = data;
    },
    
    /**
     * 创建库
     * @param {string} index 索引
     * @param {string} key 键名
     * @returns {string} 库 ID
     */
    createLibrary(index, key) {
        if (global.settings && global.settings.uuids) {
            return global.settings.uuids[key] || uuidUtils.generateUuid();
        }
        return uuidUtils.generateUuid();
    },
    
    /**
     * 转换为输出文件
     * @returns {Promise<void>}
     */
    async convertToOutputFiles() {
        // 处理所有资源文件
        await this.processAllResourceFiles();
        
        // 复制文件
        await this.copyFiles();
        
        // 转换特殊资源
        await converters.convertSpriteAtlas(this.spriteFrames);
        
        logger.info(`处理了 ${this.cacheReadList.length} 个资源文件`);
    },
    
    /**
     * 处理所有资源文件
     * @returns {Promise<void>}
     */
    async processAllResourceFiles() {
        try {
            logger.info('开始处理所有资源文件...');
            
            // 解析项目结构
            const projectStructure = await this.parseProjectStructure();

            // 仅靠编译产物恢复可读名称：先从 bundle config.*.json 读取 uuid->path
            await this.buildUuidPathMapFromBundleConfigs();
            
            // 从 bundle config 的 paths 中构建完整的目录结构（不依赖原项目）
            await this.buildDirectoryStructureFromBundleConfigs();
            
            // 统计每个bundle的资源数量
            const bundleStats = new Map();
            
            for (let filePath of this.fileList) {
                const ext = path.extname(filePath).toLowerCase();
                const fileName = path.basename(filePath);
                const fileKey = path.basename(filePath, ext);
                
                // 提取bundle名称
                const bundleName = this.extractBundleName(filePath);
                
                // 跳过 main 和 internal 这两个默认 bundle（如果用户没有自定义资源）
                // 因为它们通常只包含系统生成的编译文件
                if (bundleName === 'main' || bundleName === 'internal') {
                    if (global.verbose) {
                        logger.debug(`跳过系统 bundle: ${bundleName}`);
                    }
                    continue;
                }
                
                // 处理import目录中的序列化文件
                if (ext === '.json' && filePath.includes('import')) {
                    await this.processSerializedFile(filePath, fileName, fileKey, bundleName, projectStructure);
                } else {
                    // 处理其他资源文件，基于解析的项目结构
                    await this.processResourceFile(filePath, fileName, fileKey, bundleName, projectStructure);
                }
                
                // 更新bundle统计
                if (bundleName) {
                    bundleStats.set(bundleName, (bundleStats.get(bundleName) || 0) + 1);
                }
            }
            
            // 输出bundle统计信息
            logger.info('Bundle资源统计:');
            bundleStats.forEach((count, bundle) => {
                logger.info(`- ${bundle}: ${count} 个资源`);
            });
            
            logger.info('资源文件处理完成');
        } catch (err) {
            logger.error('处理资源文件时出错:', err);
        }
    },
    
    /**
     * 解析项目结构
     * @returns {Promise<Object>} 项目结构信息
     */
    async parseProjectStructure() {
        const structure = {
            bundles: {},
            directories: {}
        };
        
        try {
            // 1. 解析settings文件中的bundle信息
            if (global.settings && global.settings._CCSettings && global.settings._CCSettings.bundleVers) {
                const bundleVers = global.settings._CCSettings.bundleVers;
                for (const bundleName in bundleVers) {
                    structure.bundles[bundleName] = {
                        version: bundleVers[bundleName],
                        directories: []
                    };
                }
            }
            
            // 2. 扫描可选的原始资源目录结构（通过 CLI 或配置提供）
            const originalResPath = (global.paths && global.paths.originalStructureRoot) ? global.paths.originalStructureRoot : '';
            if (originalResPath && fs.existsSync(originalResPath)) {
                structure.directories = this.scanDirectoryStructure(originalResPath);
                logger.info(`成功扫描原始项目目录结构: ${originalResPath}`);
            } else if (originalResPath) {
                logger.warn(`指定的原始目录不存在: ${originalResPath}`);
            }
            
            logger.info('项目结构解析完成');
        } catch (err) {
            logger.error('解析项目结构时出错:', err);
        }
        
        return structure;
    },
    
    /**
     * 扫描目录结构
     * @param {string} dirPath 目录路径
     * @returns {Object} 目录结构
     */
    scanDirectoryStructure(dirPath) {
        const structure = {};
        
        function scan(dir, current) {
            try {
                const files = fs.readdirSync(dir);
                for (const file of files) {
                    const fullPath = path.join(dir, file);
                    const stat = fs.statSync(fullPath);
                    
                    if (stat.isDirectory()) {
                        current[file] = {};
                        scan(fullPath, current[file]);
                    }
                }
            } catch (err) {
                logger.error(`扫描目录 ${dir} 时出错:`, err);
            }
        }
        
        scan(dirPath, structure);
        return structure;
    },
    
    /**
     * 从文件路径中提取bundle名称
     * @param {string} filePath 文件路径
     * @returns {string} bundle名称
     */
    extractBundleName(filePath) {
        const assetsIndex = filePath.indexOf('assets');
        if (assetsIndex === -1) {
            return 'common';
        }
        
        const bundlePath = filePath.substring(assetsIndex + 7); // +7 to skip 'assets/'
        const bundleParts = bundlePath.split(path.sep);
        if (bundleParts.length > 0 && bundleParts[0]) {
            return bundleParts[0];
        }
        
        return 'common';
    },
    
    /**
     * 根据文件类型获取资源目录
     * @param {string} fileName 文件名
     * @param {string} ext 文件扩展名
     * @returns {string} 资源目录名
     */
    getResourceDirectory(fileName, ext) {
        ext = ext.toLowerCase();
        
        // 音频文件
        if (['.mp3', '.wav', '.ogg', '.mp4', '.m4a'].includes(ext)) {
            return 'sound';
        }
        
        // 图片文件
        if (['.png', '.jpg', '.jpeg', '.gif', '.webp'].includes(ext)) {
            return 'textures';
        }
        
        // 动画文件
        if (['.anim', '.animation'].includes(ext)) {
            return 'animation';
        }
        
        // 场景文件
        if (['.fire', '.scene'].includes(ext)) {
            return 'scenes';
        }
        
        // 预制体文件
        if (['.prefab'].includes(ext)) {
            return 'prefabs';
        }
        
        // 脚本文件
        if (['.js', '.ts', '.jsb'].includes(ext)) {
            return 'script';
        }
        
        // 特效文件
        if (['.fx', '.effect'].includes(ext)) {
            return 'effect';
        }
        
        // 其他文件
        return 'other';
    },
    
    /**
     * 处理资源文件
     * @param {string} filePath 文件路径
     * @param {string} fileName 文件名
     * @param {string} fileKey 文件键名
     * @param {string} bundleName bundle名称
     * @param {Object} projectStructure 项目结构信息
     */
    async processResourceFile(filePath, fileName, fileKey, bundleName, projectStructure) {
        const ext = path.extname(fileName);
        
        // 跳过import目录中的序列化文件，因为它们已经被processSerializedFile处理过了
        if (filePath.includes('import')) {
            return;
        }
        
        const resourceDir = this.getResourceDirectory(fileName, ext);
        // 资源 key 可能为 "<uuid>.<nativeHash>"，取前半部分作为真正的 UUID
        const uuid = fileKey;
        const uuidStem = (typeof uuid === 'string' && uuid.includes('.')) ? uuid.split('.')[0] : uuid;
        
        // 尝试从 importHashToPath 推导资源名称与相对目录（针对纹理和其他资源）
        let derivedFileName = fileName;
        let derivedSubdir = '';
        if (global.importHashToPath && typeof global.importHashToPath.get === 'function') {
            const candidates = [fileKey];
            if (typeof fileKey === 'string' && fileKey.includes('.')) {
                candidates.push(fileKey.split('.')[0]);
            }
            
            for (const cand of candidates) {
                const hit = global.importHashToPath.get(cand);
                if (hit && hit.path) {
                    // 从推导的路径提取文件名并保留扩展名
                    const baseName = path.basename(String(hit.path));
                    const nameWithoutExt = baseName.replace(/\.(prefab|fire|json|asset|png|jpg|jpeg|sprite|atlas)$/i, '');
                    // 记录相对目录（若存在）以还原层级
                    const dirPart = path.dirname(String(hit.path));
                    if (dirPart && dirPart !== '.' && dirPart !== '') {
                        derivedSubdir = dirPart;
                    }
                    if (nameWithoutExt && nameWithoutExt.length > 0) {
                        derivedFileName = nameWithoutExt + ext;
                        if (global.verbose) {
                            logger.debug(`[命名] 资源 ${fileKey} -> ${derivedFileName}`);
                        }
                        break;
                    }
                }
            }
        }

        // 其次尝试通过 uuid->path 映射恢复名称（适用于 native 纹理等非 import 资源）
        if (derivedFileName === fileName && global.uuidPathMap && typeof global.uuidPathMap.get === 'function') {
            const hit = global.uuidPathMap.get(uuidStem);
            if (hit && hit.path) {
                const baseName = path.basename(String(hit.path));
                const nameWithoutExt = baseName.replace(/\.(prefab|fire|json|asset|png|jpg|jpeg|sprite|atlas)$/i, '');
                const dirPart = path.dirname(String(hit.path));
                if (dirPart && dirPart !== '.' && dirPart !== '') {
                    derivedSubdir = dirPart;
                }
                if (nameWithoutExt && nameWithoutExt.length > 0) {
                    derivedFileName = nameWithoutExt + ext;
                    if (global.verbose) {
                        logger.debug(`[命名] UUID 映射 ${uuidStem} -> ${derivedFileName}`);
                    }
                }
            }
        }
        
        // 检查项目结构中是否存在该bundle
        const bundleExists = projectStructure.bundles && projectStructure.bundles[bundleName];
        const dirExists = projectStructure.directories && projectStructure.directories[bundleName];
        
        // 构建目标路径，基于实际项目结构
        let targetPath;
        let metaDir;
        
        if (dirExists) {
            // 如果bundle在原始目录结构中存在，保持原始结构
            const originalStructure = this.detectOriginalStructure(projectStructure.directories, bundleName);
            // 如果有 config 推导的子目录，使用它；否则直接放 bundle 根目录（不使用 resourceDir）
            const relDir = derivedSubdir ? path.join(...derivedSubdir.split(/[\/]/)) : '';
            targetPath = relDir 
                ? path.join(global.paths.output, 'assets', ...originalStructure, relDir, derivedFileName)
                : path.join(global.paths.output, 'assets', ...originalStructure, derivedFileName);
            metaDir = relDir ? path.join(...originalStructure, relDir) : path.join(...originalStructure);
        } else if (bundleExists) {
            // 如果bundle在settings中存在但目录不存在，使用bundle结构
            const relDir = derivedSubdir ? path.join(...derivedSubdir.split(/[\/]/)) : '';
            targetPath = relDir
                ? path.join(global.paths.output, 'assets', bundleName, relDir, derivedFileName)
                : path.join(global.paths.output, 'assets', bundleName, derivedFileName);
            metaDir = relDir ? path.join(bundleName, relDir) : bundleName;
        } else {
            // 否则使用默认结构
            const relDir = derivedSubdir ? path.join(...derivedSubdir.split(/[\/]/)) : '';
            targetPath = relDir
                ? path.join(global.paths.output, 'assets', 'resources', bundleName, relDir, derivedFileName)
                : path.join(global.paths.output, 'assets', 'resources', bundleName, derivedFileName);
            metaDir = relDir ? path.join('resources', bundleName, relDir) : path.join('resources', bundleName);
        }
        
        // 添加到缓存列表
        this.cacheReadList.push(filePath);
        this.cacheWriteList.push(targetPath);
        
        // 生成meta文件
        if (resourceDir !== 'other') {
            const metaData = {
                "ver": "1.2.7",
                "uuid": uuidStem,
                "optimizationPolicy": "AUTO",
                "asyncLoadAssets": false,
                "readonly": false,
                "subMetas": {}
            };
            
            fileManager.writeFile(metaDir, derivedFileName + ".meta", metaData);
        }
        
        // 分类处理
        if (resourceDir === 'sound') {
            this.audio.push({ filePath, fileName, uuid, bundleName });
        } else if (resourceDir === 'textures') {
            this.spriteFrames[fileKey] = { filePath, fileName, uuid, bundleName };
        }
    },
    
    /**
     * 处理序列化文件
     * @param {string} filePath 文件路径
     * @param {string} fileName 文件名
     * @param {string} fileKey 文件键名
     * @param {string} bundleName bundle名称
     * @param {Object} projectStructure 项目结构信息
     */
    async processSerializedFile(filePath, fileName, fileKey, bundleName, projectStructure) {
        try {
            // 读取序列化文件
            const content = await readFile(filePath, 'utf-8');
            const data = JSON.parse(content);

            // 2.4.x 常见：import 文件名可能是 md5，需要通过 config.versions.import 反查 uuid
            let assetId = fileKey;
            let derivedName = ''; // 从 importHash 推导出的名称
            const importMap = global.importHashToUuid;
            if (importMap && typeof importMap.get === 'function') {
                const candidates = [fileKey];
                if (typeof fileKey === 'string' && fileKey.includes('.')) {
                    candidates.push(fileKey.split('.')[0]);
                }

                for (const cand of candidates) {
                    const hit = importMap.get(cand);
                    if (hit && hit.uuid) {
                        assetId = hit.uuid;
                        break;
                    }
                    
                    // 同时尝试从 importHash 推导名称
                    if (!derivedName) {
                        derivedName = serializationParser.deriveNameFromImportHash(cand);
                    }
                }
            }
            
            // 解析序列化数据
            const parsedData = serializationParser.parseSerializedData(data, filePath, bundleName, assetId);
            
                if (parsedData) {
                // 根据解析结果的类型处理
                if (parsedData.__type__ === 'cc.SceneAsset') {
                    // 保存场景文件
                    serializationParser.saveSceneFile(parsedData, global.paths.output, bundleName);
                } else if (parsedData.__type__ === 'cc.Prefab') {
                    // 保存预制体文件
                    // 记录源文件名用于避免重名覆盖
                    parsedData._file = filePath;
                    parsedData._derivedName = derivedName; // 传递从 importHash 推导出的名称
                    serializationParser.savePrefabFile(parsedData, global.paths.output, bundleName);
                } else if (parsedData.__type__ === 'cc.SpriteAtlas') {
                    // 处理精灵图集，记录必要上下文，供转换器输出
                    this.spriteFrames[fileKey] = {
                        kind: 'atlas',
                        data: parsedData,
                        uuid: fileKey,
                        bundleName: bundleName || 'common',
                        sourcePath: filePath
                    };
                }
            }
        } catch (err) {
            logger.error('处理序列化文件时出错:', err);
        }
    },
    
    /**
     * 检测原始目录结构
     * @param {Object} directories 目录结构
     * @param {string} bundleName bundle名称
     * @returns {Array} 目录路径数组
     */
    detectOriginalStructure(directories, bundleName) {
        // 检查是否直接存在bundle目录
        if (directories[bundleName]) {
            return [bundleName];
        }
        
        // 检查是否存在于子目录中
        for (const dirName in directories) {
            if (typeof directories[dirName] === 'object' && directories[dirName][bundleName]) {
                return [dirName, bundleName];
            }
        }
        
        // 默认返回
        return [bundleName];
    },
    
    /**
     * 复制文件
     * @returns {Promise<void>}
     */
    async copyFiles() {
        try {
            for (let i = 0; i < this.cacheReadList.length; i++) {
                const sourcePath = this.cacheReadList[i];
                const targetPath = this.cacheWriteList[i];
                
                // 确保目标目录存在
                await fileManager.ensureDirectoryExists(path.dirname(targetPath));
                
                // 复制文件
                await fileManager.copyFile(sourcePath, targetPath);
                
                if (global.verbose) {
                    logger.debug(`复制文件: ${path.basename(sourcePath)} -> ${targetPath}`);
                }
            }
        } catch (err) {
            logger.error('复制文件时出错:', err);
            throw err;
        }
    }
};

module.exports = { resourceProcessor }; 