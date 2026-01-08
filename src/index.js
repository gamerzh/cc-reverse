/*
 * @Date: 2025-06-07 10:06:12
 * @Description: Cocos Creator 逆向工程工具入口文件
 */
const path = require('path');
const { program } = require('commander');
const { version } = require('../package.json');
const { reverseProject } = require('./core/reverseEngine');
const { logger, LogLevel } = require('./utils/logger');

// 配置命令行参数
program
  .version(version)
  .description('Cocos Creator 逆向工程工具')
  .option('-p, --path <path>', '源项目路径')
  .option('-o, --output <path>', '输出路径', './output')
  .option('-v, --verbose', '显示详细日志')
  .option('-s, --silent', '静默模式，不显示进度')
  .option('--original-structure <path>', '原始资源目录（可选），用于参考输出目录结构')
  .option('--bundle-concurrency <n>', '分析 bundle 的并发数（默认 1）', '1')
  .option('--version-hint <version>', '提示Cocos Creator版本 (2.3.x|2.4.x)', '')
  .parse(process.argv);

const options = program.opts();

// 根据 CLI 选项设置日志级别与静默模式
if (options.silent) {
  logger.setSilent(true);
}
if (options.verbose) {
  logger.setLevel(LogLevel.DEBUG);
} else {
  logger.setLevel(LogLevel.INFO);
}

// 通过命令行参数或环境变量获取路径
const sourcePath = options.path || process.env.CC_SOURCE_PATH;
if (!sourcePath) {
  logger.error('错误: 未指定源路径，请通过命令行参数 --path 或环境变量 CC_SOURCE_PATH 指定');
  logger.info('用法: node index.js --path <源项目路径>');
  process.exit(1);
}

// 开始逆向工程过程
(async () => {
  try {
    logger.info('开始处理项目...');
    await reverseProject({
      sourcePath: path.resolve(sourcePath),
      outputPath: path.resolve(options.output),
      verbose: options.verbose,
      silent: options.silent,
      originalStructure: options.originalStructure,
      bundleConcurrency: Math.max(1, parseInt(options.bundleConcurrency, 10) || 1),
      versionHint: options.versionHint
    });
    logger.success('逆向工程完成！');
  } catch (err) {
    logger.error('处理过程中出错:', err);
    process.exit(1);
  }
})(); 