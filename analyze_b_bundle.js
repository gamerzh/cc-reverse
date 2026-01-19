const fs = require('fs');
const bCfg = JSON.parse(fs.readFileSync('C:/Users/Administrator/Downloads/2026/web-mobile/assets/b/config.90522.json'));
const paths = bCfg.paths;
const types = bCfg.types;

console.log('=== B Bundle packs 分析 ===');
const packs = bCfg.packs;
for (const [importHash, indices] of Object.entries(packs)) {
    console.log(`\nImport hash: ${importHash}, indices: [${indices.join(', ')}]`);
    let prefabPath = '';
    for (const idx of indices) {
        const pathInfo = paths[idx];
        if (Array.isArray(pathInfo)) {
            const name = pathInfo[0];
            const typeIdx = pathInfo[1];
            const typeStr = types[typeIdx] || '?';
            console.log(`  [${idx}] ${name} (${typeStr})`);
            if (typeStr === 'cc.Prefab') {
                prefabPath = name;
            }
        }
    }
    if (prefabPath) {
        console.log(`  -> Expected prefab path: ${prefabPath}`);
    } else {
        console.log(`  -> No prefab found in this pack`);
    }
}
