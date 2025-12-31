<!--
 * @Date: 2025-06-07 10:06:12
 * @Description: Cocos Creator 逆向工程工具 (Python版)
-->

# cc-reverse (Python版)

Cocos Creator 逆向工程工具，用于从编译后的 Cocos Creator 游戏中提取和重建源代码与资源。

## 项目热度

如果您觉得这个项目对您有帮助，请给我们一个 Star ⭐️，这是对我们最大的鼓励！

[![Star History Chart](https://api.star-history.com/svg?repos=Crain99/cc-reverse&type=Date)](https://star-history.com/#Crain99/cc-reverse&Date)

## 功能特性

- 解析和重建 Cocos Creator 项目结构
- 提取并转换游戏脚本和资源文件
- 处理 UUID 和元数据信息
- 支持场景、预制体、动画等资源的提取
- 生成符合 Cocos Creator 格式要求的项目文件
- **支持 Cocos Creator 2.3.x 和 2.4.x 版本自动检测**

## 版本支持

### Cocos Creator 2.3.x 及以下
- 文件结构：`src/settings.js`, `src/project.js`, `res/` 目录
- 自动检测并使用相应的解析逻辑

### Cocos Creator 2.4.x
- 文件结构：支持多种构建输出格式
- 资源路径：`assets/` 或 `res/` 目录
- 配置文件：`main.js`, `settings.js`, `project.js` 等
- 使用 `--version-hint 2.4.x` 强制指定版本

## 安装 (Python 版)

### 全局安装

```bash
# 全局安装
pip install -e .

# 使用
cc-reverse --path <源项目路径>
```

### 直接运行

```bash
# 克隆仓库
git clone https://github.com/Crain99/cc-reverse.git
cd cc-reverse

# 安装依赖
pip install -r requirements.txt

# 使用
python -m cc_reverse.main --path <源项目路径>
```

## 使用方法

### 命令行参数

```
选项:
  --version            显示版本号
  -p, --path <path>    源项目路径
  -o, --output <path>  输出路径 (默认: "./output")
  -v, --verbose        显示详细日志
  -s, --silent         静默模式，不显示进度
  --version-hint <version> 提示Cocos Creator版本 (2.3.x|2.4.x)
  --help               显示帮助信息
```

### 示例

```bash
# 基本用法
python -m cc_reverse.main --path ./games/sample-game

# 指定输出目录
python -m cc_reverse.main --path ./games/sample-game --output ./extracted-game

# 显示详细日志
python -m cc_reverse.main --path ./games/sample-game --verbose

# 静默模式
python -m cc_reverse.main --path ./games/sample-game --silent

# 指定Cocos Creator版本(当自动检测失败时)
python -m cc_reverse.main --path ./games/sample-game --version-hint 2.4.x

# 处理2.4.x版本项目
python -m cc_reverse.main --path ./games/cocos24x-game --version-hint 2.4.x --verbose
```

## 配置文件

您可以在项目根目录创建 `cc-reverse.config.json` 配置文件来自定义工具行为：

```json
{
  "output": {
    "createMeta": true,
    "prettify": true,
    "includeComments": true
  },
  "codeGen": {
    "language": "typescript",
    "moduleType": "commonjs",
    "indentSize": 2,
    "indent": "space"
  },
  "assets": {
    "extractTextures": true,
    "extractAudio": true,
    "extractAnimations": true,
    "optimizeSprites": false
  }
}
```

## 注意事项

- 此工具主要用于学习和研究目的
- 无法还原经过加密的代码
- 建议先在简单的开源项目上测试（例如"合成大西瓜"）
- 请遵守相关法律法规和软件许可协议

## 项目结构

```
cc-reverse/
├── src/                     # 源代码目录
│   ├── core/                # 核心功能模块
│   │   ├── codeAnalyzer.py  # 代码分析器
│   │   ├── converters.py    # 格式转换器
│   │   ├── projectGenerator.py # 项目生成器
│   │   ├── resourceProcessor.py # 资源处理器
│   │   └── reverseEngine.py # 逆向工程引擎
│   ├── utils/              # 工具函数
│   │   ├── fileManager.py  # 文件管理工具
│   │   ├── logger.py       # 日志工具
│   │   └── uuidUtils.py    # UUID 工具
│   ├── config/             # 配置文件
│   │   └── configLoader.py # 配置加载器
│   └── __init__.py         # 包初始化文件
├── cc_reverse/             # 主入口包
│   ├── main.py             # 命令行入口
│   └── __init__.py         # 包初始化文件
├── cc-reverse.config.json  # 示例配置文件
├── setup.py                # 项目依赖配置
└── README_PYTHON.md        # Python版项目说明文档
```

## 依赖项

- rich - 终端富文本显示
- tqdm - 进度条显示
- filetype - 文件类型检测
- pillow - 图像处理
- click - 命令行参数解析
- colorama - 跨平台终端颜色支持

## 开发

```bash
# 安装依赖
pip install -r requirements-dev.txt

# 运行测试
python -m pytest

# 代码检查
python -m pylint src/
```

## 支持项目

如果您觉得这个项目对您有所帮助，请考虑给我们一个 Star ⭐️！您的支持是我们持续改进的动力。

<p align="center">
  <a href="https://github.com/Crain99/cc-reverse">
    <img src="https://img.shields.io/github/stars/Crain99/cc-reverse?style=social" alt="给项目点个Star">
  </a>
</p>

## 许可证

MIT

## 贡献

欢迎提交问题报告和改进建议！
