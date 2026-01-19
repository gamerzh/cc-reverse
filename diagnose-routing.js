#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// 读取bundle config
const configPath = path.join(__dirname, 'output', 'assets', 'a', 'config.c09f6.json');
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

console.log('\n=== Bundle Config Analysis ===\n');
console.log('paths object:');
for (const [idx, value] of Object.entries(config.paths)) {
  const pathStr = Array.isArray(value) ? value[0] : value;
  const typeIdx = Array.isArray(value) ? value[1] : undefined;
  const typeStr = typeIdx !== undefined ? (config.types[typeIdx] || 'unknown') : 'unknown';
  console.log(`  [${idx}] "${pathStr}" (type: ${typeStr})`);
}

console.log('\nuuids array:');
for (let i = 0; i < config.uuids.length; i++) {
  console.log(`  [${i}] ${config.uuids[i]}`);
}

console.log('\nversions.import mapping:');
const vImport = config.versions.import;
for (let i = 0; i < vImport.length; i += 2) {
  const idx = vImport[i];
  const hash = vImport[i + 1];
  const pathValue = config.paths[idx];
  const pathStr = Array.isArray(pathValue) ? pathValue[0] : pathValue;
  console.log(`  index ${idx} (import hash: ${hash}) -> path: "${pathStr}"`);
}

console.log('\npacks object:');
for (const [importHash, indices] of Object.entries(config.packs)) {
  const paths = indices.map(i => {
    const pathValue = config.paths[i];
    return Array.isArray(pathValue) ? pathValue[0] : pathValue;
  });
  console.log(`  import "${importHash}": [${paths.join(', ')}]`);
}

console.log('\nExpected file routing:');
console.log('  import "83dee" -> path "003/abab - 001" -> should save to: assets/a/003/abab - 001.prefab\n');
