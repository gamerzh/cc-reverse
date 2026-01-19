# cc-reverse

Cocos Creator 逆向工程工具，用于从构建后的 Web 项目中提取源代码和资源。

## 功能特性


## 输出内容

- 反序列化的资源（场景、预制体、图集等）
- 生成的 `.meta` 文件
- 基于设置的项目结构（bundles、resources 等）

### 关于资源命名（Prefab/Scene）
- Prefab/Scene 的文件名优先取自导出路径 `exportPath`，例如 `db://assets/prefabs/MyPrefab.prefab` 将输出为 `MyPrefab.prefab`。
- 当 `exportPath` 缺失时：
	- 次优先从序列化数据的 `names[]` 中推导一个可读名称；
	- 仍不可得时，尝试使用根节点名称作为文件名；
	- 最后才回退为源文件名的基名。
- 输出前会做跨平台安全化处理（替换非法字符、去除末尾空格/点），确保在 Windows 下也能成功写入。

## 安装

```bash
# 全局安装
npm install -g cc-reverse

# 或者本地安装
npm install cc-reverse
```

## 技术栈

本项目支持 **JavaScript (Node.js) 和 Python 混合开发**：
- 核心功能主要使用 **JavaScript/Node.js** 实现
- 数据处理和分析工具可使用 **Python**（优先选择更适合该任务的语言）
- 两种语言可以混用，通过子进程或 API 进行调用

在新增功能时，请根据具体需求选择最合适的语言：
- **JavaScript**: 文件 I/O、流处理、命令行工具、性能关键路径
- **Python**: 数据分析、复杂算法、机器学习相关功能、原型设计

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