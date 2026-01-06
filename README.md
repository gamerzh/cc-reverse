# Cocos Creator 逆向工程工具

一个用于逆向Cocos Creator Web编译输出的工具，能够将编译后的JavaScript代码和资源转换回可编辑的Cocos Creator项目结构。

## 功能特性

- 🔍 **自动检测**：自动检测Cocos Creator版本（2.3.x / 2.4.x）
- 📁 **完整提取**：从jsList中提取脚本文件
- 🔧 **组件分析**：分析JavaScript代码，提取cc.Class组件定义
- 📝 **脚本生成**：将分析后的组件转换为TypeScript脚本
- 📊 **资源处理**：处理和复制资源文件
- 📋 **项目生成**：生成完整的Cocos Creator项目结构
- 📄 **配置生成**：生成project.json、settings等配置文件
- 📑 **Meta文件**：自动生成.meta文件

## 支持的版本

- Cocos Creator 2.3.x
- Cocos Creator 2.4.x

## 安装

### 环境要求

- Python 3.7+
- Node.js 12+（可选，用于高级bundle处理）

### 安装步骤

1. 克隆或下载项目

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 运行工具

```bash
python -m main.main --path <CocosCreatorWeb项目路径> --output <输出路径>
```

## 使用方法

### 基本用法

```bash
python -m main.main --path <source_path> --output <output_path>
```

### 参数说明

| 参数 | 简写 | 说明 |
|------|------|------|
| --path | -p | 源项目路径（Cocos Creator Web编译输出目录） |
| --output | -o | 输出路径（生成的逆向后项目目录） |
| --verbose | -v | 显示详细日志 |
| --silent | -s | 静默模式，仅显示错误信息 |
| --version-hint | | 提示Cocos Creator版本（2.3.x / 2.4.x） |

### 示例

```bash
# 基本使用
python -m main.main --path ./cocos_web_project --output ./reverse_output

# 显示详细日志
python -m main.main --path ./cocos_web_project --output ./reverse_output --verbose

# 指定版本提示
python -m main.main --path ./cocos_web_project --output ./reverse_output --version-hint 2.4.x
```

## 项目结构

```
cc-reverse/
├── main/                 # 主程序目录
│   ├── core/             # 核心模块
│   │   ├── reverseEngine.py      # 逆向引擎主类
│   │   ├── codeAnalyzer.py       # 代码分析器
│   │   ├── projectGenerator.py   # 项目生成器
│   │   ├── resourceProcessor.py  # 资源处理器
│   │   └── bundleProcessor.py    # Bundle处理器
│   ├── tools/            # 工具模块
│   │   ├── bundle_extractor.py   # Bundle提取器
│   │   └── module_converter.py   # 模块转换器
│   ├── utils/            # 工具函数
│   │   ├── fileManager.py        # 文件管理器
│   │   └── logger.py             # 日志工具
│   └── main.py           # 主入口
├── resources_reverse/    # 资源逆向目录
│   └── resourceProcessor.py      # 资源处理器
├── code_reverse/         # 代码逆向目录
│   ├── js_analyzer/      # JavaScript分析器
│   └── py_generator/     # Python代码生成器
├── debug/                # 调试脚本
├── test_reverse.py       # 基本测试脚本
├── complex_test.py       # 复杂测试脚本
└── requirements.txt      # 依赖列表
```

## 工作流程

1. **检测版本**：自动检测Cocos Creator版本
2. **解析设置**：解析settings.js，提取jsList和配置信息
3. **分析代码**：分析JavaScript代码，提取cc.Class组件
4. **处理资源**：处理和复制资源文件
5. **生成脚本**：将组件转换为TypeScript脚本
6. **生成项目**：生成完整的Cocos Creator项目结构
7. **生成配置**：生成project.json、settings等配置文件
8. **生成Meta**：生成.meta文件

## 输出结构

```
output/
├── assets/               # 资源目录
│   ├── scripts/          # 脚本文件
│   ├── textures/         # 纹理资源
│   ├── sounds/           # 音频资源
│   └── ...               # 其他资源
├── settings/             # 设置目录
│   ├── editor.json       # 编辑器配置
│   └── project.json      # 项目配置
├── project.json          # 项目主配置
├── package.json          # 包配置
├── library/              # 库目录（空）
└── temp/                 # 临时目录（空）
```

## 注意事项

1. 本工具仅用于学习和研究目的，请勿用于非法用途
2. 由于Cocos Creator编译过程中的代码压缩和混淆，逆向结果可能不完全准确
3. 对于复杂的项目，可能需要手动调整生成的代码
4. 部分高级功能可能需要Node.js环境
5. 对于加密或特殊处理的bundle文件，处理效果可能有限

## 调试

使用--verbose参数查看详细日志：

```bash
python -m main.main --path <source_path> --output <output_path> --verbose
```

## 测试

### 基本测试

```bash
python test_reverse.py
```

### 复杂测试

```bash
python complex_test.py
```

## 常见问题

### Q: 工具无法检测到Cocos Creator版本怎么办？
A: 使用--version-hint参数手动指定版本，如--version-hint 2.4.x

### Q: 生成的代码有错误怎么办？
A: 检查原始JavaScript代码是否被压缩或混淆严重，可能需要手动调整生成的代码

### Q: 资源文件没有被处理怎么办？
A: 确保源项目中存在assets或res目录，并且包含资源文件

### Q: 出现编码错误怎么办？
A: 工具已添加编码回退机制，会尝试多种编码格式，如仍有问题，请检查源文件编码

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 更新日志

### 0.1.0
- 初始版本
- 支持Cocos Creator 2.3.x和2.4.x
- 实现基本的逆向功能
- 支持脚本提取和组件分析
- 支持资源处理和项目生成

### 0.1.1
- 修复了编码问题
- 改进了settings解析
- 增强了组件检测能力
- 优化了资源处理
- 增加了测试脚本

## 联系方式

如有问题或建议，欢迎通过以下方式联系：

- GitHub: [https://github.com/yourusername/cc-reverse](https://github.com/yourusername/cc-reverse)
- Email: your.email@example.com
