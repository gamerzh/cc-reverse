# cc-reverse

Cocos Creator 逆向工程工具，用于从构建后的 Web 项目中提取源代码和资源。

## 功能特性

- 支持 Cocos Creator 2.3.x 和 2.4.x 版本
- 提取和还原 TypeScript 源代码
- 处理和转换资源文件
- 生成 Cocos Creator 项目配置文件
- 支持子包处理

## 安装

```bash
# 全局安装
npm install -g cc-reverse

# 或者本地安装
npm install cc-reverse
```

## 使用方法

```bash
# 基本用法
cc-reverse --path <源项目路径>

# 自定义输出路径
cc-reverse --path <源项目路径> --output <输出路径>

# 指定 Cocos Creator 版本
cc-reverse --path <源项目路径> --version-hint 2.4.x

# 指定原始资源目录（可选，用于参考输出目录结构）
cc-reverse --path <源项目路径> --original-structure <原始assets/res路径>

# 设置 bundle 分析并发数（默认 1）
cc-reverse --path <源项目路径> --bundle-concurrency 4

# 显示详细日志
cc-reverse --path <源项目路径> --verbose
```

## 示例

```bash
# 从构建后的 Web 项目中提取代码和资源
cc-reverse --path ./build/web-mobile --output ./output
```

## 注意事项

- 该工具仅用于学习和研究目的
- 请遵守相关法律法规，不要用于商业用途
- 对于复杂项目，可能需要手动调整生成的代码和资源