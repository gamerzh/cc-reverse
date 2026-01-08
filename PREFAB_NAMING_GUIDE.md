# Prefab 文件名还原指南

## 为什么生成的 prefab 文件名是字母和数字？

### 问题原因

您看到的 prefab 文件名（如 `2e8888b7.49350.prefab`）是**哈希值**，这是因为工具无法从编译后的数据中找到原始的可读名称。

### Cocos Creator 编译后的变化

当 Cocos Creator 编译项目时：

1. **原始项目**（编译前）:
   ```
   assets/res/fhpoker/prefabs/
   ├── BetPanel.prefab          ← 可读名称
   ├── BetPanel.prefab.meta     ← 包含 UUID
   ├── CardItem.prefab
   └── CardItem.prefab.meta
   ```

2. **编译后的输出**:
   ```
   build/web-mobile/assets/fhpoker/import/
   ├── 2e/2e8888b7-3760-4764-9a69-c8f7f036444f.json
   ├── 4a/4a12345c-1234-5678-abcd-ef1234567890.json
   └── ...
   ```

编译后的 JSON 文件：
- **文件名变成了 UUID 的哈希值**（不可读）
- **内部数据通常不包含原始文件名**
- 只有通过 UUID 才能映射回原始名称

---

## 命名恢复的优先级策略

工具按以下优先级尝试恢复名称：

### 1. **exportPath**（最可靠）
```javascript
data[8] = "db://assets/prefabs/BetPanel.prefab"
```
- **仅在 2.3.x** 中可用
- **2.4.x 中通常为 `undefined`**

### 2. **rawAssets 映射**
```javascript
global.settings._CCSettings.rawAssets.assets = {
  "2e8888b7-3760-4764-9a69-c8f7f036444f": ["prefabs/BetPanel", ...]
}
```
- 需要正确解析 `settings.js`
- 并非所有资源都在 rawAssets 中

### 3. **原始目录结构映射**（推荐方法）⭐
```javascript
// 通过 --original-structure 参数指定编译前的目录
BetPanel.prefab.meta → uuid: "2e8888b7-3760-4764-9a69-c8f7f036444f"
```
- **最有效的方法**
- 需要提供原始 `assets/res` 目录

### 4. **names[] 数组**
```javascript
data[2] = ["BetPanel", "node", "_spriteFrame"]
```
- 包含各种内部名称
- 可能是属性名而非文件名

### 5. **深度扫描数据**
```javascript
// 在数据中查找 "db://assets/..." 路径
```
- 不一定存在
- 可能误匹配

### 6. **根节点名称**
```javascript
prefabData._root._name = "BetPanel"
```
- 可能是 `"Node"` 等通用名
- 已过滤无意义名称

### 7. **导入文件名**（fallback）
```javascript
"2e8888b7.49350.json" → "2e8888b7.49350.prefab"
```
- 最后的兜底方案
- **这就是您现在看到的结果**

---

## 解决方案：使用 --original-structure

### 步骤 1: 准备原始项目目录

您需要提供**编译前**的原始项目目录，包含 `.prefab` 和 `.prefab.meta` 文件：

```
C:\Workflow\xsh5\assets\res\
├── fhpoker\
│   └── prefabs\
│       ├── BetPanel.prefab
│       ├── BetPanel.prefab.meta   ← 包含 uuid
│       ├── CardItem.prefab
│       └── CardItem.prefab.meta
├── guandan\
└── hall\
```

### 步骤 2: 运行工具时指定参数

```bash
cc-reverse --path "C:\Workflow\xsh5\build\web-mobile" \
           --output "./output" \
           --original-structure "C:\Workflow\xsh5\assets\res" \
           --version-hint "2.4.x" \
           --verbose
```

### 步骤 3: 查看诊断日志

使用 `--verbose` 参数后，您会看到详细的命名诊断信息：

```
[命名诊断] 文件: 2e8888b7.49350.json
[命名诊断] bundle: fhpoker, uuids数量: 3
[命名诊断] 缓存中UUID数量: 24, 基础名数量: 24
[命名诊断] ✓ 通过文件名UUID匹配成功: BetPanel (uuid: 2e8888b7...)
```

或者失败时：

```
[命名诊断] ✗ 文件名UUID (4a12345c...) 在缓存中未找到
[命名诊断] ✗ 所有匹配方法都失败，无法还原名称
```

---

## 常见问题诊断

### ❌ 问题 1: "缓存中UUID数量: 0"

**原因**: 原始目录路径不正确或没有 `.prefab.meta` 文件

**解决方案**:
```bash
# 检查路径是否存在
dir "C:\Workflow\xsh5\assets\res\fhpoker\prefabs"

# 确保有 .prefab.meta 文件
dir "C:\Workflow\xsh5\assets\res\fhpoker\prefabs\*.meta"
```

### ❌ 问题 2: "文件名UUID在缓存中未找到"

**原因**: 
1. **UUID 不匹配**: 编译后的 UUID 与原始 meta 文件中的 UUID 不一致
2. **2.4.x UUID 编码问题**: 某些版本使用 22 字符压缩格式

**解决方案**:
```bash
# 查看一个实际的 import JSON 文件名
dir "C:\Workflow\xsh5\build\web-mobile\assets\fhpoker\import" | Select-Object -First 5

# 查看对应的 .prefab.meta 内容
Get-Content "C:\Workflow\xsh5\assets\res\fhpoker\prefabs\BetPanel.prefab.meta" | ConvertFrom-Json
```

对比 JSON 文件名的 UUID 前缀是否与 meta 中的 `uuid` 字段匹配。

### ❌ 问题 3: "bundle 不匹配"

**原因**: 工具检测到的 bundle 名称与原始目录结构中的不一致

**解决方案**: 工具已经放宽了 bundle 匹配规则（允许 `common` bundle），通常不需要担心。

---

## 2.4.x vs 2.3.x 的区别

| 特性 | 2.3.x | 2.4.x |
|------|-------|-------|
| **exportPath** | ✅ 通常存在于 `data[8]` | ❌ 通常为 `undefined` |
| **项目布局** | `res/import/...` | `assets/<bundle>/import/...` |
| **UUID 格式** | 标准 36 字符 | 可能是 22 字符压缩格式 |
| **uuids[] 内容** | 包含 prefab 自己的 uuid | ❌ 仅包含依赖资源的 uuid |
| **命名恢复难度** | 简单 | 困难（需要 original-structure） |

---

## 验证是否成功

运行工具后检查输出：

```bash
# 成功的输出示例
[INFO] 保存预制体文件: ...\assets\fhpoker\prefabs\BetPanel.prefab  ← 可读名称
[INFO] 保存预制体文件: ...\assets\fhpoker\prefabs\CardItem.prefab

# 失败的输出示例  
[INFO] 保存预制体文件: ...\assets\common\prefabs\2e8888b7.49350.prefab  ← 哈希名称
```

如果您看到可读名称，说明映射成功！

---

## 总结

**为什么是字母和数字？**
- 因为 Cocos Creator 编译后丢失了原始文件名
- 编译后的数据只包含 UUID 和内部引用

**如何恢复？**
- **必须**使用 `--original-structure` 参数
- 指向编译前的 `assets/res` 目录
- 工具会通过 `.prefab.meta` 的 UUID 进行映射

**如果还是失败？**
- 使用 `--verbose` 查看诊断日志
- 检查 UUID 是否匹配
- 确认原始目录结构正确
- 提供具体的日志输出以便进一步诊断
