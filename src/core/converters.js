/*
 * @Date: 2025-06-07 10:06:12
 * @Description: 资源格式转换工具
 */
const path = require('path');
const fs = require('fs');
const { promisify } = require('util');
const XMLWriter = require('xml-writer');
const sizeOf = require('image-size');
const imageinfo = require('imageinfo');
const { uuidUtils } = require('../utils/uuidUtils');
const { fileManager } = require('../utils/fileManager');
const { logger } = require('../utils/logger');

// 将 fs 的异步方法转换为 Promise
const readFile = promisify(fs.readFile);
const writeFile = promisify(fs.writeFile);

/**
 * 资源格式转换工具
 */
const converters = {
    /**
     * 转换精灵图集
     * @param {Object} spriteFrames 精灵帧对象
     * @returns {Promise<void>}
     */
    async convertSpriteAtlas(spriteFrames) {
        try {
            logger.info('处理精灵图集...');

            // 遍历 spriteFrames，筛选 atlas 类型的条目
            for (const key of Object.keys(spriteFrames || {})) {
                const entry = spriteFrames[key];
                if (!entry || entry.kind !== 'atlas' || !entry.data) continue;

                const atlas = entry.data; // 由解析器返回的 SpriteAtlas 数据
                const atlasName = (atlas._name && String(atlas._name)) || key;
                const bundleName = entry.bundleName || 'common';

                // 目标输出目录: assets/<bundle>/textures/
                const outDir = path.join(global.paths.output, 'assets', bundleName, 'textures');
                await fileManager.ensureDirectoryExists(outDir);

                // 构造 TexturePacker 风格 JSON（最小化），含 metadata + frames
                const frames = {};
                if (atlas._spriteFrames && typeof atlas._spriteFrames === 'object') {
                    for (const fname of Object.keys(atlas._spriteFrames)) {
                        const f = atlas._spriteFrames[fname];
                        const rect = (f && f._rect) || { x: 0, y: 0, width: 0, height: 0 };
                        const offset = (f && f._offset) || { x: 0, y: 0 };
                        const orig = (f && f._originalSize) || { width: 0, height: 0 };
                        const rotated = !!(f && f._rotated);
                        frames[fname + '.png'] = {
                            frame: { x: rect.x || 0, y: rect.y || 0, w: rect.width || 0, h: rect.height || 0 },
                            offset: { x: offset.x || 0, y: offset.y || 0 },
                            rotated: rotated,
                            sourceColorRect: { x: rect.x || 0, y: rect.y || 0, w: rect.width || 0, h: rect.height || 0 },
                            sourceSize: { w: orig.width || 0, h: orig.height || 0 },
                            spriteSourceSize: { w: rect.width || 0, h: rect.height || 0 }
                        };
                    }
                }

                // 构造 metadata，定位并引用 PNG 纹理
                const fileBase = path.join(outDir, atlasName);
                const expectedPng = fileBase + '.png';

                // 默认引用 atlasName.png；若不存在，尝试在已复制纹理中查找
                let textureFileName = path.basename(expectedPng);
                let textureFullPath = expectedPng;

                if (!fs.existsSync(expectedPng)) {
                    const found = this.findExistingTextureForAtlas(spriteFrames, atlasName, bundleName);
                    if (found && fs.existsSync(found.outputFullPath)) {
                        textureFileName = found.fileName;
                        textureFullPath = found.outputFullPath;
                    } else if (found && fs.existsSync(found.sourceFullPath)) {
                        // 源文件存在但未复制（少见），复制到输出目录并引用
                        await fileManager.ensureDirectoryExists(outDir);
                        await fileManager.copyFile(found.sourceFullPath, path.join(outDir, found.fileName));
                        textureFileName = found.fileName;
                        textureFullPath = path.join(outDir, found.fileName);
                    } else {
                        // 作为兜底，再尝试 common 目录
                        const commonCandidate = path.join(global.paths.output, 'assets', 'common', 'textures', atlasName + '.png');
                        if (fs.existsSync(commonCandidate)) {
                            textureFileName = path.basename(commonCandidate);
                            textureFullPath = commonCandidate;
                        }
                    }
                }

                const plistJson = {
                    frames,
                    metadata: {
                        format: 3,
                        pixelFormat: 'RGBA8888',
                        premultiplyAlpha: false,
                        realTextureFileName: textureFileName,
                        size: this.getImageSizeByPath(textureFullPath),
                        smartupdate: `$TexturePacker:SmartUpdate:${uuidUtils.generateUuid()}:${uuidUtils.generateUuid()}:${uuidUtils.generateUuid()}$`,
                        textureFileName: textureFileName
                    },
                    animations: {}
                };

                // 生成 XML/PLIST
                const xml = this.createXmlDocument(plistJson);
                const plistPath = fileBase + '.plist';
                await writeFile(plistPath, xml.toString());

                // 写入 meta 文件
                const metaData = {
                    ver: '1.2.7',
                    uuid: entry.uuid || uuidUtils.generateUuid(),
                    optimizationPolicy: 'AUTO',
                    asyncLoadAssets: false,
                    readonly: false,
                    subMetas: {}
                };
                await fileManager.writeFile(path.join(bundleName, 'textures'), atlasName + '.plist.meta', metaData);

                logger.info(`输出图集: ${plistPath}`);
            }
        } catch (err) {
            logger.error('转换精灵图集时出错:', err);
        }
    },
    
    /**
     * 在已处理的纹理条目中查找与图集同名或同 bundle 的 png
     * 返回源路径与输出路径，便于直接引用或复制。
     */
    findExistingTextureForAtlas(spriteFrames, atlasName, bundleName) {
        try {
            const values = Object.values(spriteFrames || {}).filter(v => !v || v.kind !== 'atlas');
            // 优先：同 bundle、同名（不含扩展名）
            let candidate = values.find(v => v && v.bundleName === bundleName && path.basename(v.fileName, path.extname(v.fileName)) === atlasName);
            if (!candidate) {
                // 次选：任意 bundle、同名
                candidate = values.find(v => v && path.basename(v.fileName, path.extname(v.fileName)) === atlasName);
            }
            if (!candidate) return null;

            const sourceFullPath = candidate.filePath;
            const outputFullPath = path.join(global.paths.output, 'assets', candidate.bundleName || 'common', 'textures', candidate.fileName);
            return {
                fileName: candidate.fileName,
                sourceFullPath,
                outputFullPath
            };
        } catch (e) {
            return null;
        }
    },
    
    /**
     * 将 JSON 转换为 PLIST 格式
     * @param {string} fileName 文件名（不含扩展名）
     * @returns {Promise<void>}
     */
    async jsonToPlist(fileName) {
        try {
            // 读取 JSON 文件
            const data = await readFile(fileName + '.json', 'utf-8');
            const json = JSON.parse(data);
            
            // 添加必要的属性
            const enhancedJson = this.addProperties(json, fileName);
            
            // 创建 XML 文档
            const xml = this.createXmlDocument(enhancedJson);
            
            // 写入 PLIST 文件
            await writeFile(fileName + '.plist', xml.toString());
            
            logger.debug(`转换完成: ${fileName}.json -> ${fileName}.plist`);
        } catch (err) {
            logger.error(`转换文件 ${fileName} 时出错:`, err);
        }
    },
    
    /**
     * 创建 XML 文档
     * @param {Object} json JSON 对象
     * @returns {XMLWriter} XML 文档对象
     */
    createXmlDocument(json) {
        const xml = new XMLWriter();
        
        // 初始化文档
        xml.startDocument();
        xml.writeDocType('plist', "-//Apple Computer//DTD PLIST 1.0//EN", "http://www.apple.com/DTDs/PropertyList-1.0.dtd");
        
        // 开始 PLIST 元素
        xml.startElement('plist');
        xml.writeAttribute('version', "1.0");
        
        // 写入主字典
        xml.startElement('dict');
        this.parsetoXML(xml, json);
        
        // 结束文档
        xml.endElement(); // dict
        xml.endElement(); // plist
        xml.endDocument();
        
        return xml;
    },
    
    /**
     * 将 JSON 对象解析为 XML
     * @param {XMLWriter} xml XML 写入器
     * @param {Object} json JSON 对象
     */
    parsetoXML(xml, json) {
        for (const key in json) {
            const value = json[key];
            
            if (typeof value === "object") {
                // 写入键
                xml.startElement('key');
                xml.text(key);
                xml.endElement();
                
                // 处理特殊格式的对象
                if (key === 'frame' || key === 'offset' || key === 'sourceColorRect' || 
                    key === 'sourceSize' || key === 'spriteSourceSize') {
                    this.parsetoJson(xml, value);
                } else {
                    // 处理一般对象
                    xml.startElement('dict');
                    this.parsetoXML(xml, value);
                    xml.endElement();
                }
            } else {
                // 处理基本类型值
                this.toXML(xml, key, value);
            }
        }
    },
    
    /**
     * 将基本类型的键值对写入 XML
     * @param {XMLWriter} xml XML 写入器
     * @param {string} key 键
     * @param {*} value 值
     */
    toXML(xml, key, value) {
        // 写入键
        xml.startElement('key');
        xml.text(key);
        xml.endElement();
        
        // 根据值类型写入不同标签
        if (typeof value === 'boolean') {
            // 布尔值
            xml.startElement(value.toString());
        } else if (typeof value === "number") {
            // 数字
            xml.startElement('integer');
            xml.text(value.toString());
        } else {
            // 字符串或其他
            xml.startElement('string');
            xml.text(value.toString());
        }
        
        xml.endElement();
    },
    
    /**
     * 将对象解析为特定格式的 JSON 字符串
     * @param {XMLWriter} xml XML 写入器
     * @param {Object} value 值对象
     */
    parsetoJson(xml, value) {
        xml.startElement('string');
        
        let json;
        if (value.x !== undefined && value.w !== undefined) {
            // 包含位置和尺寸的对象
            json = `{{${value.x},${value.y}},{${value.w},${value.h}}}`;
        } else {
            // 仅包含尺寸的对象
            json = `{${value.w},${value.h}}`;
        }
        
        xml.text(json);
        xml.endElement();
    },
    
    /**
     * 添加必要的属性到 JSON 对象
     * @param {Object} json JSON 对象
     * @param {string} fileName 文件名
     * @returns {Object} 增强后的 JSON 对象
     */
    addProperties(json, fileName) {
        // 创建元数据
        const metadata = {
            format: 3,
            pixelFormat: "RGBA8888",
            premultiplyAlpha: false,
            realTextureFileName: path.basename(fileName) + '.png',
            size: this.getImageSize(fileName),
            smartupdate: `$TexturePacker:SmartUpdate:${uuidUtils.generateUuid()}:${uuidUtils.generateUuid()}:${uuidUtils.generateUuid()}$`,
            textureFileName: path.basename(fileName) + '.png'
        };
        
        // 将元数据添加到 JSON
        const result = { ...json };
        result['metadata'] = metadata;
        
        // 删除旧的元数据
        if (result['meta']) {
            delete result['meta'];
        }
        
        return result;
    },
    
    /**
     * 获取图像尺寸
     * @param {string} fileName 文件名
     * @returns {string} 格式化的尺寸字符串
     */
    getImageSize(fileName) {
        try {
            const filedata = fs.readFileSync(fileName + '.png');
            const info = imageinfo(filedata);
            return `{${info.width},${info.height}}`;
        } catch (err) {
            logger.error(`读取图像文件 ${fileName}.png 时出错:`, err);
            return '{0,0}';
        }
    },

    /**
     * 通过完整路径获取图像尺寸（存在即读，不存在返回 {0,0}）
     */
    getImageSizeByPath(fullPath) {
        try {
            if (!fullPath || !fs.existsSync(fullPath)) return '{0,0}';
            const filedata = fs.readFileSync(fullPath);
            const info = imageinfo(filedata);
            return `{${info.width},${info.height}}`;
        } catch (err) {
            logger.error(`读取图像文件 ${fullPath} 时出错:`, err);
            return '{0,0}';
        }
    }
};

module.exports = { converters }; 