/*
 * @Date: 2026-01-07 10:06:12
 * @Description: Cocos Creator 序列化数据解析器
 */
const fs = require('fs');
const path = require('path');
const { logger } = require('../utils/logger');
const { fileManager } = require('../utils/fileManager');
const { uuidUtils } = require('../utils/uuidUtils');

/**
 * 序列化数据解析器
 */
const serializationParser = {
    originalPrefabCache: null,
    originalPrefabCacheRoot: '',
    /**
     * 解析序列化的资源数据
     * @param {Array} data 序列化数据
     * @param {string} filePath 文件路径
     * @returns {Object} 解析后的资源对象
     */
    parseSerializedData(data, filePath, bundleName, assetId) {
        try {
            if (!Array.isArray(data)) {
                logger.warn('序列化数据格式错误，不是数组，已跳过:', filePath);
                return null;
            }

            const version = data[0];
            const uuids = data[1];
            const names = data[2];
            const types = data[3];
            const typeIndices = data[4];
            const objects = data[5];
            const assets = data[6];
            const depends = data[7];
            const exportPath = data[8];
            const isScene = data[9];

            logger.debug(`解析序列化数据 - 版本: ${version}, 资源数量: ${objects ? objects.length : 0}`);

            // 从多种来源推导资源原名：exportPath -> rawAssets -> bundle config -> 原始目录 -> names[] -> data 深扫 -> 根节点 -> 文件名
            let exportName = this.deriveNameFromExportPath(exportPath);
            const rawAssetName = this.deriveNameFromRawAssets(Array.isArray(uuids) ? uuids : []);
            const bundleConfigName = this.deriveNameFromBundleConfig(assetId, bundleName);
            const originalStructName = this.deriveNameFromOriginalStructure(filePath, bundleName, Array.isArray(uuids) ? uuids : []);
            if (!exportName) {
                exportName = rawAssetName || bundleConfigName || originalStructName || this.deriveNameFromDataDeep(data) || '';
            }
            const namesArr = Array.isArray(names) ? names : [];

            // 根据类型处理不同的资源
            const includesTypeDeep = (node, needle) => {
                if (!node) return false;
                if (typeof node === 'string') return node.includes(needle);
                if (Array.isArray(node)) return node.some(n => includesTypeDeep(n, needle));
                if (typeof node === 'object') return Object.values(node).some(v => includesTypeDeep(v, needle));
                return false;
            };

            if (types) {
                // 检查是否是预制体文件（优先）
                const isPrefabFile = Array.isArray(types) && types.some(type => 
                    (typeof type === 'string' && type.includes('cc.Prefab')) ||
                    (typeof type === 'object' && includesTypeDeep(type, 'cc.Prefab'))
                );
                
                if (isPrefabFile || includesTypeDeep(data, 'cc.Prefab')) {
                    return this.parsePrefabData(data, filePath, exportName, namesArr, rawAssetName, originalStructName);
                }
                
                // 检查是否是场景文件
                // 只有当明确标记为场景文件时才处理为场景
                const isSceneFile = data[9] === true && Array.isArray(types) && types.some(type => 
                    (typeof type === 'string' && type.includes('cc.SceneAsset')) ||
                    (typeof type === 'object' && includesTypeDeep(type, 'cc.SceneAsset'))
                );
                
                if (isSceneFile) {
                    return this.parseSceneData(data, filePath, exportName);
                }
                
                // 检查是否是精灵图集文件
                if (Array.isArray(types)) {
                    for (let i = 0; i < types.length; i++) {
                        const type = types[i];
                        if ((typeof type === 'string' && type.includes('cc.SpriteAtlas')) ||
                            (typeof type === 'object' && includesTypeDeep(type, 'cc.SpriteAtlas'))) {
                            return this.parseSpriteAtlasData(data, filePath, exportName);
                        }
                    }
                }
            }

            return this.parseGeneralAsset(data, filePath);
        } catch (err) {
            logger.error('解析序列化数据时出错:', err);
            return null;
        }
    },

    /**
     * 解析场景数据
     * @param {Array} data 序列化数据
     * @param {string} filePath 文件路径
     * @returns {Object} 场景对象
     */
    parseSceneData(data, filePath, exportName) {
        try {
            logger.info('解析场景数据:', filePath);
            
            const objects = data[5];
            const sceneData = {
                __type__: 'cc.SceneAsset',
                _name: exportName || path.basename(filePath, path.extname(filePath)),
                _root: null,
                _nodes: []
            };

            // 解析节点数据
            if (objects) {
                for (let i = 0; i < objects.length; i++) {
                    const obj = objects[i];
                    if (Array.isArray(obj)) {
                        const nodeData = this.parseNodeData(obj);
                        if (nodeData) {
                            sceneData._nodes.push(nodeData);
                            if (!sceneData._root) {
                                sceneData._root = nodeData;
                            }
                        }
                    }
                }
            }

            return sceneData;
        } catch (err) {
            logger.error('解析场景数据时出错:', err);
            return null;
        }
    },

    /**
     * 解析预制体数据
     * @param {Array} data 序列化数据
     * @param {string} filePath 文件路径
     * @returns {Object} 预制体对象
     */
    parsePrefabData(data, filePath, exportName, namesArr, rawAssetName, originalStructName) {
        try {
            logger.info('解析预制体数据:', filePath);
            
            const objects = data[5];
            const prefabData = {
                __type__: 'cc.Prefab',
                _name: exportName || rawAssetName || originalStructName || this.deriveNameFromNames(Array.isArray(namesArr) ? namesArr : []) || this.deriveNameFromDataDeep(data) || path.basename(filePath, path.extname(filePath)),
                _root: null,
                _nodes: [],
                _bindings: [],
                _customProperties: {}
            };

            // 解析节点数据
            if (objects) {
                for (let i = 0; i < objects.length; i++) {
                    const obj = objects[i];
                    if (Array.isArray(obj)) {
                        const nodeData = this.parseNodeData(obj);
                        if (nodeData) {
                            prefabData._nodes.push(nodeData);
                            if (!prefabData._root) {
                                prefabData._root = nodeData;
                            }
                        }
                    }
                }
            }

            // 若无 exportPath 且可获取根节点名称，则用根节点名作为可读名（但过滤掉无意义名称）
            if ((!exportName || exportName.length === 0) && prefabData._root && prefabData._root._name) {
                const rootNameRaw = prefabData._root._name;
                const rootName = (typeof rootNameRaw === 'string') ? rootNameRaw.trim() : '';
                if (this.isMeaningfulAssetName(rootName)) {
                    prefabData._name = rootName;
                }
            }

            return prefabData;
        } catch (err) {
            logger.error('解析预制体数据时出错:', err);
            return null;
        }
    },

    /**
     * 解析精灵图集数据
     * @param {Array} data 序列化数据
     * @param {string} filePath 文件路径
     * @returns {Object} 精灵图集对象
     */
    parseSpriteAtlasData(data, filePath, exportName) {
        try {
            logger.info('解析精灵图集数据:', filePath);
            
            const objects = data[5];
            const spriteAtlasData = {
                __type__: 'cc.SpriteAtlas',
                _name: exportName || path.basename(filePath, path.extname(filePath)),
                _spriteFrames: {},
                _texture: null
            };

            // 解析精灵帧数据
            if (objects) {
                for (let i = 0; i < objects.length; i++) {
                    const obj = objects[i];
                    if (Array.isArray(obj)) {
                        const spriteFrameData = this.parseSpriteFrameData(obj);
                        if (spriteFrameData) {
                            const frameName = spriteFrameData._name || `frame_${i}`;
                            spriteAtlasData._spriteFrames[frameName] = spriteFrameData;
                        }
                    }
                }
            }

            return spriteAtlasData;
        } catch (err) {
            logger.error('解析精灵图集数据时出错:', err);
            return null;
        }
    },

    /**
     * 解析节点数据
     * @param {Array} data 节点数据
     * @returns {Object} 节点对象
     */
    parseNodeData(data) {
        try {
            const nodeData = {
                __type__: 'cc.Node',
                _name: 'Node',
                _position: { x: 0, y: 0 },
                _rotation: 0,
                _scale: { x: 1, y: 1 },
                _anchorPoint: { x: 0.5, y: 0.5 },
                _size: { width: 100, height: 100 },
                _color: { r: 255, g: 255, b: 255, a: 255 },
                _opacity: 255,
                _skewX: 0,
                _skewY: 0,
                _children: [],
                _components: []
            };

            // 解析节点属性
            if (data[0]) {
                // 解析名称
                if (data[0][0]) {
                    nodeData._name = data[0][0];
                }

                // 解析位置
                if (data[0][1]) {
                    nodeData._position = { x: data[0][1][0], y: data[0][1][1] };
                }

                // 解析旋转
                if (data[0][2] !== undefined) {
                    nodeData._rotation = data[0][2];
                }

                // 解析缩放
                if (data[0][3]) {
                    nodeData._scale = { x: data[0][3][0], y: data[0][3][1] };
                }

                // 解析大小
                if (data[0][4]) {
                    nodeData._size = { width: data[0][4][0], height: data[0][4][1] };
                }
            }

            return nodeData;
        } catch (err) {
            logger.error('解析节点数据时出错:', err);
            return null;
        }
    },

    /**
     * 解析精灵帧数据
     * @param {Array} data 精灵帧数据
     * @returns {Object} 精灵帧对象
     */
    parseSpriteFrameData(data) {
        try {
            const spriteFrameData = {
                __type__: 'cc.SpriteFrame',
                _name: 'SpriteFrame',
                _rect: { x: 0, y: 0, width: 0, height: 0 },
                _offset: { x: 0, y: 0 },
                _originalSize: { width: 0, height: 0 },
                _rotated: false,
                _texture: null
            };

            // 解析精灵帧属性
            if (data[0]) {
                // 解析名称
                if (data[0][0]) {
                    spriteFrameData._name = data[0][0];
                }

                // 解析矩形
                if (data[0][1]) {
                    spriteFrameData._rect = {
                        x: data[0][1][0],
                        y: data[0][1][1],
                        width: data[0][1][2],
                        height: data[0][1][3]
                    };
                }

                // 解析偏移
                if (data[0][2]) {
                    spriteFrameData._offset = { x: data[0][2][0], y: data[0][2][1] };
                }

                // 解析原始大小
                if (data[0][3]) {
                    spriteFrameData._originalSize = { width: data[0][3][0], height: data[0][3][1] };
                }

                // 解析旋转
                if (data[0][4] !== undefined) {
                    spriteFrameData._rotated = data[0][4];
                }
            }

            return spriteFrameData;
        } catch (err) {
            logger.error('解析精灵帧数据时出错:', err);
            return null;
        }
    },

    /**
     * 解析通用资源
     * @param {Array} data 序列化数据
     * @param {string} filePath 文件路径
     * @returns {Object} 资源对象
     */
    parseGeneralAsset(data, filePath) {
        try {
            const assetType = this.detectAssetType(data);
            const assetName = path.basename(filePath, path.extname(filePath));

            const asset = {
                __type__: assetType,
                _name: assetName,
                _file: filePath
            };

            logger.debug(`解析通用资源 - 类型: ${assetType}, 名称: ${assetName}`);
            return asset;
        } catch (err) {
            logger.error('解析通用资源时出错:', err);
            return null;
        }
    },

    /**
     * 检测资源类型
     * @param {Array} data 序列化数据
     * @returns {string} 资源类型
     */
    detectAssetType(data) {
        const types = data[3];
        if (types) {
            for (const type of types) {
                if (type.includes('cc.')) {
                    return type;
                }
            }
        }
        return 'cc.Asset';
    },

    /**
     * 保存解析后的场景文件
     * @param {Object} sceneData 场景数据
     * @param {string} outputPath 输出路径
     * @param {string} bundleName bundle名称
     */
    saveSceneFile(sceneData, outputPath, bundleName) {
        try {
            const sceneName = this.sanitizeFileName(sceneData._name || 'scene');
            const scenePath = path.join(outputPath, 'assets', bundleName, 'scenes', `${sceneName}.fire`);
            
            fileManager.writeFile(path.join(bundleName, 'scenes'), `${sceneName}.fire`, sceneData);
            fileManager.writeFile(path.join(bundleName, 'scenes'), `${sceneName}.fire.meta`, this.generateMetaFile(sceneData));
            
            logger.info(`保存场景文件: ${scenePath}`);
        } catch (err) {
            logger.error('保存场景文件时出错:', err);
        }
    },

    /**
     * 保存解析后的预制体文件
     * @param {Object} prefabData 预制体数据
     * @param {string} outputPath 输出路径
     * @param {string} bundleName bundle名称
     */
    savePrefabFile(prefabData, outputPath, bundleName) {
        try {
            const rawName = (typeof prefabData._name === 'string') ? prefabData._name : '';
            const baseName = this.sanitizeFileName(this.isMeaningfulAssetName(rawName) ? rawName : '');
            const dir = path.join(outputPath, 'assets', bundleName, 'prefabs');

            // 若名称过于通用，使用源文件名作为更稳定的 fallback，避免覆盖
            const sourceKey = this.sanitizeFileName(path.basename(prefabData._file || '', path.extname(prefabData._file || '')));
            let prefabName = baseName;
            if (!prefabName || prefabName === 'asset' || prefabName === 'Node' || /\[object\s+Object\]/i.test(prefabName)) {
                prefabName = sourceKey || prefabName || 'prefab';
            }

            // 如果目标文件已存在，追加后缀确保唯一
            let finalName = prefabName;
            const suffixBase = (sourceKey || 'prefab').replace(/\./g, '_');
            let counter = 1;
            while (fs.existsSync(path.join(dir, `${finalName}.prefab`))) {
                const short = suffixBase.slice(0, 8) || String(counter);
                finalName = `${prefabName}_${short}_${counter}`;
                counter += 1;
            }

            const prefabPath = path.join(outputPath, 'assets', bundleName, 'prefabs', `${finalName}.prefab`);
            
            fileManager.writeFile(path.join(bundleName, 'prefabs'), `${finalName}.prefab`, prefabData);
            fileManager.writeFile(path.join(bundleName, 'prefabs'), `${finalName}.prefab.meta`, this.generateMetaFile(prefabData));
            
            logger.info(`保存预制体文件: ${prefabPath}`);
        } catch (err) {
            logger.error('保存预制体文件时出错:', err);
        }
    },

    /**
     * 生成meta文件数据
     * @param {Object} assetData 资源数据
     * @returns {Object} meta文件数据
     */
    generateMetaFile(assetData) {
        return {
            "ver": "1.2.7",
            "uuid": assetData._uuid || require('uuid').v4(),
            "optimizationPolicy": "AUTO",
            "asyncLoadAssets": false,
            "readonly": false,
            "subMetas": {}
        };
    },

    /**
     * 从 exportPath 推导资源名称（去后缀）
     * 例如 db://assets/prefabs/MyPrefab.prefab -> MyPrefab
     */
    deriveNameFromExportPath(exportPath) {
        try {
            if (!exportPath || typeof exportPath !== 'string') return '';
            // 去掉协议前缀 db://
            const cleaned = exportPath.replace(/^db:\/\//, '');
            const base = path.basename(cleaned);
            const name = base.replace(/\.(prefab|fire|json|asset)$/i, '');
            return name || '';
        } catch (e) {
            return '';
        }
    },

    /**
     * 深度遍历序列化数据，寻找包含 .prefab/.fire 或 /prefabs/、/scenes/ 的字符串，提取可读名
     */
    deriveNameFromDataDeep(node) {
        try {
            const stack = [node];
            while (stack.length) {
                const cur = stack.pop();
                if (typeof cur === 'string') {
                    const s = cur;
                    // 优先匹配 db://assets 路径
                    let m = s.match(/db:\/\/assets\/[A-Za-z0-9_\-\/.]+\.(prefab|fire)/i);
                    if (m) {
                        const base = path.basename(m[0]);
                        return base.replace(/\.(prefab|fire)$/i, '');
                    }
                    // 次选匹配 /prefabs/ or /scenes/ 片段
                    m = s.match(/\/(prefabs|scenes)\/[A-Za-z0-9_\-\.]+/i);
                    if (m) {
                        const base = path.basename(m[0]);
                        return base.replace(/\.(prefab|fire)$/i, '');
                    }
                    // 直接包含 .prefab/.fire
                    m = s.match(/[A-Za-z0-9_\-\.]+\.(prefab|fire)/i);
                    if (m) {
                        const base = path.basename(m[0]);
                        const name = base.replace(/\.(prefab|fire)$/i, '');
                        // 排除类型名如 cc.Prefab 被误判
                        if (name.toLowerCase() === 'cc') return '';
                        return name;
                    }
                } else if (Array.isArray(cur)) {
                    for (let i = 0; i < cur.length; i++) stack.push(cur[i]);
                } else if (cur && typeof cur === 'object') {
                    for (const v of Object.values(cur)) stack.push(v);
                }
            }
            return '';
        } catch {
            return '';
        }
    },

    /**
     * 从 _CCSettings.rawAssets 中根据 uuid 推导名称
     */
    deriveNameFromRawAssets(uuids) {
        try {
            if (!Array.isArray(uuids) || uuids.length === 0) return '';
            const settings = global.settings && (global.settings._CCSettings || global.settings.CCSettings);
            if (!settings || !settings.rawAssets || !settings.rawAssets.assets) return '';
            const assets = settings.rawAssets.assets;
            for (const id of uuids) {
                const entry = assets[id];
                if (entry && entry[0]) {
                    const url = Array.isArray(entry) ? entry[0] : entry.url || '';
                    if (typeof url === 'string' && url.length) {
                        const base = path.basename(url);
                        return base.replace(/\.(prefab|fire|json|asset)$/i, '');
                    }
                }
            }
            return '';
        } catch {
            return '';
        }
    },

    /**
     * 预扫描原始目录结构，缓存 uuid -> 名称 映射（prefabs）
     */
    buildOriginalPrefabCache() {
        try {
            const origRoot = global.paths && global.paths.originalStructureRoot;
            if (!origRoot || !fs.existsSync(origRoot)) {
                this.originalPrefabCache = { byUuid: {}, byBase: {} };
                this.originalPrefabCacheRoot = origRoot || '';
                return;
            }

            const byUuid = {};
            const byBase = {};
            const walk = dir => {
                const entries = fs.readdirSync(dir, { withFileTypes: true });
                for (const ent of entries) {
                    const full = path.join(dir, ent.name);
                    if (ent.isDirectory()) {
                        walk(full);
                        continue;
                    }

                    if (ent.name.endsWith('.prefab.meta')) {
                        const base = path.basename(ent.name, '.prefab.meta');
                        const rel = path.relative(origRoot, full);
                        const parts = rel.split(path.sep);
                        const bundle = parts.length > 0 ? parts[0] : '';
                        try {
                            const meta = JSON.parse(fs.readFileSync(full, 'utf8'));
                            if (meta && typeof meta.uuid === 'string') {
                                byUuid[meta.uuid] = { name: base, bundle };
                            }
                        } catch {
                            // ignore malformed meta
                        }
                        byBase[base] = { name: base, bundle };
                    } else if (ent.name.endsWith('.prefab')) {
                        const base = path.basename(ent.name, '.prefab');
                        const rel = path.relative(origRoot, full);
                        const parts = rel.split(path.sep);
                        const bundle = parts.length > 0 ? parts[0] : '';
                        byBase[base] = { name: base, bundle };
                    }
                }
            };

            walk(origRoot);
            this.originalPrefabCache = { byUuid, byBase };
            this.originalPrefabCacheRoot = origRoot;
        } catch {
            this.originalPrefabCache = { byUuid: {}, byBase: {} };
            this.originalPrefabCacheRoot = '';
        }
    },

    /**
     * 从原始目录结构（originalStructureRoot）推导名称，基于 uuid / 文件名
     */
    deriveNameFromOriginalStructure(filePath, bundleName, uuids) {
        try {
            const origRoot = global.paths && global.paths.originalStructureRoot;
            if (!origRoot || !Array.isArray(uuids)) return '';
            if (!this.originalPrefabCache || this.originalPrefabCacheRoot !== origRoot) {
                this.buildOriginalPrefabCache();
            }
            const cache = this.originalPrefabCache || { byUuid: {}, byBase: {} };

            const bundleMatch = (hitBundle) => (!hitBundle || !bundleName || hitBundle === bundleName || bundleName === 'common');

            // 诊断日志：显示正在尝试匹配的信息
            if (global.verbose) {
                logger.debug(`[命名诊断] 文件: ${path.basename(filePath)}`);
                logger.debug(`[命名诊断] bundle: ${bundleName}, uuids数量: ${uuids.length}`);
                logger.debug(`[命名诊断] 缓存中UUID数量: ${Object.keys(cache.byUuid).length}, 基础名数量: ${Object.keys(cache.byBase).length}`);
            }

            for (const id of uuids) {
                const key = (typeof id === 'string' && id.length === 22) ? (uuidUtils.decodeUuid(id) || id) : id;
                const hit = cache.byUuid[key];
                if (hit && bundleMatch(hit.bundle)) {
                    if (global.verbose) {
                        logger.debug(`[命名诊断] ✓ 通过uuids[]匹配成功: ${hit.name} (uuid: ${key.substring(0, 8)}...)`);
                    }
                    return hit.name;
                }
            }

            // 2.4.x 常见情况：uuids[] 是依赖资源列表，不包含当前 prefab 自己的 uuid。
            // 这时尝试用 import 文件名里的 uuid（第一个点之前）去匹配原始 prefab.meta。
            const fileStem = path.basename(filePath, path.extname(filePath));
            const stemUuid = fileStem.split('.')[0];
            if (stemUuid) {
                const key = (stemUuid.length === 22) ? (uuidUtils.decodeUuid(stemUuid) || stemUuid) : stemUuid;
                const hit = cache.byUuid[key];
                if (hit && bundleMatch(hit.bundle)) {
                    if (global.verbose) {
                        logger.debug(`[命名诊断] ✓ 通过文件名UUID匹配成功: ${hit.name} (uuid: ${key.substring(0, 8)}...)`);
                    }
                    return hit.name;
                } else if (global.verbose) {
                    logger.debug(`[命名诊断] ✗ 文件名UUID (${stemUuid.substring(0, 8)}...) 在缓存中未找到`);
                }
            }

            const baseNoExt = path.basename(filePath, path.extname(filePath));
            const hitBase = cache.byBase[baseNoExt];
            if (hitBase && bundleMatch(hitBase.bundle)) {
                if (global.verbose) {
                    logger.debug(`[命名诊断] ✓ 通过基础名匹配成功: ${hitBase.name}`);
                }
                return hitBase.name;
            }

            if (global.verbose) {
                logger.debug(`[命名诊断] ✗ 所有匹配方法都失败，无法还原名称`);
            }
            return '';
        } catch (e) {
            if (global.verbose) {
                logger.debug(`[命名诊断] ✗ 异常: ${e.message}`);
            }
            return '';
        }
    },

    /**
     * 从编译产物的 bundle config.*.json 建立的 uuid->path 映射中推导名称（无需编译前对照）。
     * 常见：path 为 "prefabs/Foo" 或 "scenes/Main"，此处取 basename 作为资源名。
     */
    deriveNameFromBundleConfig(assetId, bundleName) {
        try {
            const map = global.uuidPathMap;
            if (!map || typeof map.get !== 'function') return '';
            if (!assetId || typeof assetId !== 'string') return '';

            const stem = assetId.split('.')[0];
            const key = (stem.length === 22) ? (uuidUtils.decodeUuid(stem) || stem) : stem;

            const hit = map.get(key);
            if (!hit || !hit.path) return '';

            // bundle 只做弱约束：允许 common 或未标注
            if (hit.bundle && bundleName && hit.bundle !== bundleName && bundleName !== 'common') {
                // 不直接拒绝：有些构建会把资源打进不同 bundle
            }

            const base = path.basename(String(hit.path));
            const name = base.replace(/\.(prefab|fire|json|asset)$/i, '');
            return name || '';
        } catch {
            return '';
        }
    },

    /**
     * 判断名称是否“像一个资源名”，避免 Node / [object Object] / 属性名 等无意义内容
     */
    isMeaningfulAssetName(name) {
        if (!name || typeof name !== 'string') return false;
        const s = name.trim();
        if (!s) return false;
        if (s === 'Node' || s === 'asset') return false;
        if (/\[object\s+Object\]/i.test(s)) return false;
        // 2.4.x 解析时可能得到数组/对象字符串化后的逗号串，通常不是好名字
        if (/^\d+,/.test(s)) return false;
        // 常见属性名（来自 names[]）
        const lower = s.toLowerCase();
        const bad = new Set(['node', 'root', 'data', '_spriteframe', '_texturesetter', '_defaultclip', '_name']);
        if (bad.has(lower)) return false;
        return true;
    },

    /**
     * 从 names 数组粗略推导人类可读名称
     */
    deriveNameFromNames(namesArr) {
        try {
            if (!Array.isArray(namesArr)) return '';
            const cand = namesArr.find(s => typeof s === 'string' && /[A-Za-z\u4e00-\u9fa5]/.test(s));
            if (!cand) return '';
            return cand.replace(/\.(prefab|fire|json|asset)$/i, '');
        } catch {
            return '';
        }
    },

    /**
     * 使文件名在各平台下安全
     */
    sanitizeFileName(name) {
        if (!name || typeof name !== 'string') return 'asset';
        let safe = name.trim().replace(/[<>:\"\/\\|?*]/g, '_');
        safe = safe.replace(/[\s\.]+$/g, '');
        if (safe.length === 0) safe = 'asset';
        return safe;
    }
};

module.exports = { serializationParser };