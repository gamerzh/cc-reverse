#!/usr/bin/env node

const path = require('path');
const fs = require('fs');
const { codeAnalyzer } = require('./src/core/codeAnalyzer');

// 清理旧的输出
const outputPath = path.join(__dirname, 'output-test');
if (fs.existsSync(outputPath)) {
  console.log('Removing old output directory...');
  const { execSync } = require('child_process');
  try {
    execSync(`rmdir /s /q "${outputPath}"`, { stdio: 'ignore' });
  } catch (e) {
    // 忽略错误
  }
}

// 设置全局变量
global.paths = {
  res: path.join(__dirname, 'test-data', '2026', 'web-mobile', 'res'),
  output: outputPath,
  settings: path.join(__dirname, 'test-data', '2026', 'web-mobile', 'settings.json')
};
global.verbose = true;

(async () => {
  try {
    const projectPath = path.join(__dirname, 'test-data', '2026', 'web-mobile');
    console.log('Starting analysis from:', projectPath);
    console.log('Output to:', outputPath);
    await codeAnalyzer.analyzeProject(projectPath);
    console.log('\n✓ Analysis complete!\n');
  } catch (e) {
    console.error('✗ Error:', e.message);
    console.error(e.stack);
    process.exit(1);
  }
})();
