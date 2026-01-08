#!/usr/bin/env node
/**
 * Prefab 命名诊断工具
 * 帮助诊断为什么 prefab 文件名无法还原
 */

const fs = require('fs');
const path = require('path');

function diagnose(buildPath, originalPath) {
    console.log('='.repeat(60));
    console.log('Prefab 命名诊断工具');
    console.log('='.repeat(60));
    console.log('');

    // 检查构建目录
    console.log('1️⃣  检查构建目录...');
    if (!fs.existsSync(buildPath)) {
        console.error(`❌ 构建目录不存在: ${buildPath}`);
        return;
    }
    console.log(`✅ 构建目录存在: ${buildPath}`);
    console.log('');

    // 检查原始目录
    console.log('2️⃣  检查原始目录...');
    if (!fs.existsSync(originalPath)) {
        console.error(`❌ 原始目录不存在: ${originalPath}`);
        console.log('   请提供正确的编译前 assets/res 目录路径');
        return;
    }
    console.log(`✅ 原始目录存在: ${originalPath}`);
    console.log('');

    // 扫描原始 prefab
    console.log('3️⃣  扫描原始 prefab 文件...');
    const originalPrefabs = [];
    const scanOriginal = (dir) => {
        const entries = fs.readdirSync(dir, { withFileTypes: true });
        for (const ent of entries) {
            const full = path.join(dir, ent.name);
            if (ent.isDirectory()) {
                scanOriginal(full);
            } else if (ent.name.endsWith('.prefab.meta')) {
                const prefabName = path.basename(ent.name, '.prefab.meta');
                const metaPath = full;
                try {
                    const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
                    if (meta && meta.uuid) {
                        originalPrefabs.push({
                            name: prefabName,
                            uuid: meta.uuid,
                            path: path.relative(originalPath, full)
                        });
                    }
                } catch (e) {
                    console.warn(`⚠️  无法解析 meta: ${metaPath}`);
                }
            }
        }
    };
    scanOriginal(originalPath);
    console.log(`✅ 找到 ${originalPrefabs.length} 个原始 prefab`);
    originalPrefabs.slice(0, 5).forEach(p => {
        console.log(`   - ${p.name} (${p.uuid.substring(0, 8)}...)`);
    });
    if (originalPrefabs.length > 5) {
        console.log(`   ... 还有 ${originalPrefabs.length - 5} 个`);
    }
    console.log('');

    // 扫描编译后的 import JSON
    console.log('4️⃣  扫描编译后的 import JSON...');
    const importFiles = [];
    const scanImport = (dir) => {
        if (!fs.existsSync(dir)) return;
        const entries = fs.readdirSync(dir, { withFileTypes: true });
        for (const ent of entries) {
            const full = path.join(dir, ent.name);
            if (ent.isDirectory()) {
                scanImport(full);
            } else if (ent.name.endsWith('.json')) {
                try {
                    const content = fs.readFileSync(full, 'utf8');
                    const data = JSON.parse(content);
                    if (Array.isArray(data) && data[3]) {
                        const types = data[3];
                        const isPrefab = types.some(t => 
                            (typeof t === 'string' && t.includes('cc.Prefab'))
                        );
                        if (isPrefab) {
                            const filename = path.basename(full, '.json');
                            const uuidPrefix = filename.split('.')[0];
                            importFiles.push({
                                filename,
                                uuidPrefix,
                                path: path.relative(buildPath, full),
                                uuids: data[1] || [],
                                exportPath: data[8]
                            });
                        }
                    }
                } catch (e) {
                    // 忽略无效的 JSON
                }
            }
        }
    };

    // 尝试多种可能的目录结构
    const possiblePaths = [
        path.join(buildPath, 'res', 'import'),
        path.join(buildPath, 'assets'),
    ];
    
    for (const p of possiblePaths) {
        scanImport(p);
    }

    console.log(`✅ 找到 ${importFiles.length} 个 prefab import JSON`);
    importFiles.slice(0, 5).forEach(f => {
        console.log(`   - ${f.filename} (uuids: ${f.uuids.length}, exportPath: ${f.exportPath ? '有' : '无'})`);
    });
    if (importFiles.length > 5) {
        console.log(`   ... 还有 ${importFiles.length - 5} 个`);
    }
    console.log('');

    // 尝试匹配
    console.log('5️⃣  尝试 UUID 匹配...');
    const uuidMap = new Map();
    originalPrefabs.forEach(p => {
        uuidMap.set(p.uuid, p.name);
        // 也尝试压缩格式的 UUID（2.4.x）
        const compressed = compressUuid(p.uuid);
        if (compressed) {
            uuidMap.set(compressed, p.name);
        }
    });

    let matchCount = 0;
    let noMatchCount = 0;
    
    console.log('');
    console.log('匹配结果示例:');
    console.log('-'.repeat(60));
    
    importFiles.slice(0, 10).forEach(f => {
        let matched = false;
        let matchMethod = '';

        // 方法 1: 通过文件名 UUID 前缀
        if (uuidMap.has(f.uuidPrefix)) {
            matched = true;
            matchMethod = '文件名UUID';
            matchCount++;
            console.log(`✅ ${f.filename}`);
            console.log(`   → ${uuidMap.get(f.uuidPrefix)} (通过${matchMethod})`);
        } 
        // 方法 2: 通过 uuids[] 数组
        else {
            for (const uuid of f.uuids) {
                if (uuidMap.has(uuid)) {
                    matched = true;
                    matchMethod = 'uuids[]';
                    matchCount++;
                    console.log(`✅ ${f.filename}`);
                    console.log(`   → ${uuidMap.get(uuid)} (通过${matchMethod})`);
                    break;
                }
            }
        }

        if (!matched) {
            noMatchCount++;
            console.log(`❌ ${f.filename}`);
            console.log(`   → 无法匹配 (uuidPrefix: ${f.uuidPrefix.substring(0, 8)}..., uuids: ${f.uuids.length}个)`);
        }
    });

    console.log('-'.repeat(60));
    console.log('');
    console.log('📊 匹配统计:');
    console.log(`   成功匹配: ${matchCount}/${importFiles.length}`);
    console.log(`   无法匹配: ${noMatchCount}/${importFiles.length}`);
    console.log('');

    // 给出建议
    console.log('6️⃣  诊断结果与建议:');
    if (matchCount === 0) {
        console.log('❌ 没有任何匹配成功！');
        console.log('');
        console.log('可能的原因:');
        console.log('1. 原始目录路径不正确（不是编译前的 assets/res 目录）');
        console.log('2. UUID 格式不匹配（2.4.x 可能使用不同的编码）');
        console.log('3. 构建目录与原始目录来自不同的项目');
        console.log('');
        console.log('请检查:');
        console.log(`- 原始目录是否是编译前的源代码目录？`);
        console.log(`- 构建目录是否是从这个原始目录编译生成的？`);
    } else if (matchCount === importFiles.length) {
        console.log('✅ 所有 prefab 都可以成功匹配！');
        console.log('');
        console.log('运行工具时请使用:');
        console.log(`cc-reverse --path "${buildPath}" \\`);
        console.log(`           --output "./output" \\`);
        console.log(`           --original-structure "${originalPath}" \\`);
        console.log(`           --version-hint "2.4.x" \\`);
        console.log(`           --verbose`);
    } else {
        console.log(`⚠️  部分 prefab 可以匹配 (${matchCount}/${importFiles.length})`);
        console.log('');
        console.log('这是正常的，可能的原因:');
        console.log('1. 某些 prefab 是运行时动态生成的');
        console.log('2. 某些资源不在原始目录中');
        console.log('3. 编译过程中有一些临时资源');
        console.log('');
        console.log('运行工具时请使用:');
        console.log(`cc-reverse --path "${buildPath}" \\`);
        console.log(`           --output "./output" \\`);
        console.log(`           --original-structure "${originalPath}" \\`);
        console.log(`           --version-hint "2.4.x" \\`);
        console.log(`           --verbose`);
    }

    console.log('');
    console.log('='.repeat(60));
}

// 简化的 UUID 压缩函数（用于诊断）
function compressUuid(uuid) {
    if (!uuid || uuid.length !== 36) return null;
    // 简化版本，仅用于诊断
    return uuid.replace(/-/g, '').substring(0, 22);
}

// CLI
const args = process.argv.slice(2);
if (args.length < 2) {
    console.log('使用方法:');
    console.log('  node diagnose-prefab-naming.js <构建目录> <原始目录>');
    console.log('');
    console.log('示例:');
    console.log('  node diagnose-prefab-naming.js "C:\\Workflow\\xsh5\\build\\web-mobile" "C:\\Workflow\\xsh5\\assets\\res"');
    process.exit(1);
}

diagnose(args[0], args[1]);
