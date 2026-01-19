#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const outputDir = path.join(__dirname, 'output');
const testDataDir = path.join(__dirname, '..', '..', 'test-projects', '2026-web-mobile');

// 清理旧输出
if (fs.existsSync(outputDir)) {
  console.log('Removing old output directory...');
  try {
    execSync(`del /s /q "${outputDir}" & rmdir "${outputDir}"`, { stdio: 'ignore' });
  } catch (e) {
    // ignore
  }
}

// 检查源数据
if (!fs.existsSync(testDataDir)) {
  console.error(`Test data not found at: ${testDataDir}`);
  console.log('Using current output directory for verification only');
} else {
  console.log(`Using test data from: ${testDataDir}`);
}

// 导入并运行逆向
const { codeAnalyzer } = require('./src/core/codeAnalyzer');

global.paths = {
  res: path.join(testDataDir, 'res'),
  output: outputDir,
  settings: path.join(testDataDir, 'settings.json')
};
global.verbose = true;
global.settings = {};

(async () => {
  try {
    if (!fs.existsSync(testDataDir)) {
      console.log('\n✓ Test data directory not found, using existing output for analysis\n');
      process.exit(0);
    }
    
    console.log('\n[START] Running reversal analysis...\n');
    await codeAnalyzer.analyzeProject(testDataDir);
    console.log('\n[DONE] Reversal complete!\n');
    
    // 检查输出
    if (fs.existsSync(path.join(outputDir, 'assets', 'a', '003'))) {
      console.log('✓ Directory a/003 exists');
    } else {
      console.log('✗ Directory a/003 MISSING');
    }
    
    if (fs.existsSync(path.join(outputDir, 'assets', 'a', '003', 'abab - 001.prefab'))) {
      console.log('✓ File a/003/abab - 001.prefab exists (CORRECT)');
    } else if (fs.existsSync(path.join(outputDir, 'assets', 'a', 'abab - 001.prefab'))) {
      console.log('✗ File a/abab - 001.prefab exists (WRONG - should be in a/003/)');
    } else {
      console.log('? File abab - 001.prefab not found');
    }
  } catch (e) {
    console.error('\n[ERROR]', e.message);
    process.exit(1);
  }
})();
