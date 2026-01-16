# cc-reverse 改进日志

## 最新改进：从 Bundle Config 恢复资源原始名称

### 问题
逆向工程生成的预制体文件使用 hash 命名，而不是原始的人类可读名称。例如：
- 生成：`0871242d4.0f3df.prefab` 
- 期望：`Money.prefab`

### 原因
1. Cocos Creator 编译过程中，资源被打包到 bundle 中
2. import/*.json 文件使用 hash 名称（如 `0b55cf59e.a065f.json`）
3. 原始资源名称在编译产物的 bundle config.*.json 中保存

### 解决方案

#### 1. 增强 `buildUuidPathMapFromBundleConfigs()`
- **新增 `importHashToPath` 全局映射**：从 import hash 直接映射到资源路径名
- **解析 packs 字段**：`packs[importHash] = [assetIndex1, assetIndex2, ...]`
- **类型识别**：根据 `types[]` 数组识别资源类型，优先选择 `cc.Prefab`
- **智能选择**：当一个 import 文件包含多个资源时，优先使用 prefab 类型的资源名

#### 2. 新增辅助函数（在 `serializationParser.js`）
```javascript
// 从 importHash 推导单个资源名称
deriveNameFromImportHash(importHash)

// 从 importHash 推导所有资源名称
deriveNamesFromImportHash(importHash)
```

#### 3. 改进 `processJsonFiles()`
- 检测 import 文件（路径包含 `/import/`）
- 提取 import hash（文件名第一个点之前的部分）
- 通过 `deriveNameFromImportHash()` 推导资源名称

#### 4. 改进 `processSerializedFile()`
- 传递推导出的 `derivedName` 给 `parsedData._derivedName`
- 后续处理时优先使用这个名称

#### 5. 改进 `savePrefabFile()`
- 优先使用 `prefabData._derivedName`（从 importHash 推导）
- 其次使用原始 JSON 中的 `_name` 字段
- 最后才使用源文件名作为 fallback

### 技术细节

#### Bundle Config 结构
```json
{
  "paths": {
    "0": ["winter", 2],          // 名称 -> 类型索引
    "2": ["abab", 0],
    "3": ["Money", 0]
  },
  "types": ["cc.Prefab", "cc.SpriteFrame", "cc.Texture2D"],
  "uuids": ["uuid1", "uuid2", ...],
  "packs": {
    "0b55cf59e": [2, 4],         // importHash -> 资源索引数组
    "0871242d4": [2, 3, 4]
  },
  "versions": {
    "import": [2, "0b55cf59e", 3, "0871242d4", ...],  // 索引 <-> hash 映射
    "native": [...]
  }
}
```

#### 映射流程
```
import/*.json 文件名 (如 0b55cf59e.a065f.json)
           ↓
    提取 importHash (0b55cf59e)
           ↓
    查询 packs[0b55cf59e] = [assetIndices]
           ↓
    遍历 assetIndices，查询 paths[index]
           ↓
    检查 types[typeIndex]，优先选择 cc.Prefab
           ↓
    返回资源名称 (如 "abab")
           ↓
    生成 abab.prefab ✅
```

### 改进效果

#### 生成对比

**改进前：**
```
assets/
├── a/prefabs/
│   └── 0b55cf59e.a065f.prefab   ❌ Hash 名称
└── b/prefabs/
    └── 0871242d4.0f3df.prefab   ❌ Hash 名称
```

**改进后：**
```
assets/
├── a/prefabs/
│   └── abab.prefab              ✅ 原始名称
└── b/prefabs/
    └── Money.prefab             ✅ 原始名称
```

#### 日志输出改进
```
[INFO] [命名映射] 从 bundle config 建立 importHash->path 映射数量: 10
[INFO] 保存预制体文件: C:\...\assets\a\prefabs\abab.prefab
[INFO] 保存预制体文件: C:\...\assets\b\prefabs\Money.prefab
```

### 代码修改清单

1. **resourceProcessor.js**
   - 初始化 `importHashToPath: new Map()`
   - 增强 `buildUuidPathMapFromBundleConfigs()` 处理 packs 和类型识别
   - 改进 `processJsonFiles()` 提取 import hash
   - 改进 `processSerializedFile()` 传递推导名称

2. **serializationParser.js**
   - 新增 `deriveNameFromImportHash()`
   - 新增 `deriveNamesFromImportHash()`
   - 改进 `savePrefabFile()` 使用推导名称

### 优势

✅ **自动化恢复**：无需保留原始项目，仅从编译产物恢复
✅ **准确性高**：基于官方的 bundle metadata，而不是启发式猜测
✅ **完整支持**：处理多资源包、优先级选择、类型识别
✅ **向后兼容**：原有的 fallback 逻辑保持不变
✅ **可扩展**：映射结构支持后续处理其他资源类型

### 后续优化空间

- [ ] 为其他资源类型（SpriteFrame、Texture2D）生成文件时也使用推导名称
- [ ] 缓存 importHash->path 映射，加快大型项目的处理速度
- [ ] 支持自定义命名规则
- [ ] 处理名称冲突（多个资源同名时的策略）
