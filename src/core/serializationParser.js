/*
 * @Date: 2026-01-07 10:06:12
 * @Description: Cocos Creator 序列化数据解析器
 */
const path = require('path');
const { logger } = require('../utils/logger');
const { fileManager } = require('../utils/fileManager');

/**
 * 序列化数据解析器
 */
const serializationParser = {
    /**
     * 解析序列化的资源数据
     * @param {Array} data 序列化数据
     * @param {string} filePath 文件路径
     * @returns {Object} 解析后的资源对象
     */
    parseSerializedData(data, filePath) {
        try {
            if (!Array.isArray(data)) {
                logger.error('序列化数据格式错误，不是数组:', filePath);
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

            // 根据类型处理不同的资源
            if (types) {
                // 检查是否是场景文件
                const isSceneFile = data[9] === true || types.some(type => type.includes('cc.SceneAsset'));
                
                if (isSceneFile) {
                    return this.parseSceneData(data, filePath);
                }
                
                // 检查是否是预制体文件
                for (let i = 0; i < types.length; i++) {
                    const type = types[i];
                    if (type.includes('cc.Prefab')) {
                        return this.parsePrefabData(data, filePath);
                    } else if (type.includes('cc.SpriteAtlas')) {
                        return this.parseSpriteAtlasData(data, filePath);
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
    parseSceneData(data, filePath) {
        try {
            logger.info('解析场景数据:', filePath);
            
            const objects = data[5];
            const sceneData = {
                __type__: 'cc.SceneAsset',
                _name: path.basename(filePath, path.extname(filePath)),
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
    parsePrefabData(data, filePath) {
        try {
            logger.info('解析预制体数据:', filePath);
            
            const objects = data[5];
            const prefabData = {
                __type__: 'cc.Prefab',
                _name: path.basename(filePath, path.extname(filePath)),
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
    parseSpriteAtlasData(data, filePath) {
        try {
            logger.info('解析精灵图集数据:', filePath);
            
            const objects = data[5];
            const spriteAtlasData = {
                __type__: 'cc.SpriteAtlas',
                _name: path.basename(filePath, path.extname(filePath)),
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
            const sceneName = sceneData._name || 'scene';
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
            const prefabName = prefabData._name || 'prefab';
            const prefabPath = path.join(outputPath, 'assets', bundleName, 'prefabs', `${prefabName}.prefab`);
            
            fileManager.writeFile(path.join(bundleName, 'prefabs'), `${prefabName}.prefab`, prefabData);
            fileManager.writeFile(path.join(bundleName, 'prefabs'), `${prefabName}.prefab.meta`, this.generateMetaFile(prefabData));
            
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
    }
};

module.exports = { serializationParser };