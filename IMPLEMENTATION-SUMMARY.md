# Implementation Summary: Prefab File Placement Fix

## Issue
用户报告 CCReverse 工具的目录结构问题："为什么003目录下的abab - 001没有在003下而是在a下"

This indicates that prefab files were not being placed in their correct subdirectories as specified in the bundle configuration.

## Root Analysis
1. **Directory Structure**: ✓ CORRECT  
   - `a/003/` directory is properly created from bundle config declaration `"003/abab - 001"`
   
2. **File Placement**: ✗ BROKEN
   - File `abab - 001.prefab` placed in `a/` instead of `a/003/`
   - Even though bundle config shows: `"3": ["003/abab - 001", 0]` → `types[0]` = `cc.Prefab`

## Why This Happened
The `processSerializedFile()` method (which handles prefabs from import directory) was not properly passing subdirectory information to `savePrefabFile()`. The code lacked the logic to:
1. Map import file → UUID
2. Map UUID → resource path (containing subdirectory info)
3. Pass subdirectory to file save operation

## Solution Implemented

### File: `src/core/resourceProcessor.js`

#### Function: `processSerializedFile()` (lines 1119-1226)

**Changes:**
1. **Added UUID Lookup**: Access `global.uuidPathMap` to look up UUID → full resource path
   ```javascript
   const uuidPathMap = global.uuidPathMap;
   if (uuidPathMap && typeof uuidPathMap.get === 'function') {
       const pathByUuid = uuidPathMap.get(assetId);
       if (pathByUuid) {
           derivedPath = pathByUuid.path || pathByUuid;
           // ... extract name from path
       }
   }
   ```

2. **Improved Fallback Chain**:
   - Primary: uuidPathMap lookup (most reliable)
   - Secondary: importHashToPath lookup
   - Tertiary: bundlePathsMap name matching
   - Fallback: serializationParser derivation

3. **Added Logging**: Debug output for file routing decisions when `global.verbose` is enabled
   ```javascript
   logger.info(`[文件路由] 从UUID '${assetId}' 获取路径: '${derivedPath}'`);
   ```

4. **Pass Metadata**: Attach subdirectory info to prefabData
   ```javascript
   parsedData._derivedName = derivedName;
   parsedData._derivedPath = derivedPath; // ← key for subdirectory extraction
   ```

#### Function: `buildUuidPathMapFromBundleConfigs()` (lines 88-298)
- Already correctly builds UUID → path mappings from bundle config
- No changes needed

#### Function: `buildDirectoryStructureFromBundleConfigs()` (lines 315-398)
- Already correctly creates directory hierarchy per bundle
- No changes needed

### File: `src/core/serializationParser.js`

#### Function: `savePrefabFile()` (line 424)

**Changes:**
1. **Use derivedPath metadata**:
   ```javascript
   const derivedPath = (typeof prefabData._derivedPath === 'string') 
       ? prefabData._derivedPath : '';
   const derivedSubdir = derivedPath ? path.dirname(derivedPath) : '';
   ```

2. **Added Logging**: Output subdirectory extraction when verbose mode is on
   ```javascript
   if (global.verbose && derivedPath) {
       logger.info(`[prefab保存] 资源路径: "${derivedPath}", 子目录: "${derivedSubdir}"...`);
   }
   ```

3. **Create Output Path**: Use extracted subdirectory
   ```javascript
   const dir = path.join(outputPath, 'assets', bundleName, ...dirParts);
   ```

## Example Flow After Fix

```
Input: import file "83dee.xxx.json" in bundle "a"

Step 1: Identify UUID
  importHashToUuid.get("83dee") 
  → { uuid: "4fyraXpfdGZYZ9t+2ao7YI", bundle: "a" }
  assetId = "4fyraXpfdGZYZ9t+2ao7YI"

Step 2: Map UUID to Resource Path
  uuidPathMap.get("4fyraXpfdGZYZ9t+2ao7YI")
  → { path: "003/abab - 001", bundle: "a" }
  derivedPath = "003/abab - 001"
  derivedName = "abab - 001"

Step 3: Parse Serialized Data
  parseSerializedData(...) → prefabData object
  
Step 4: Attach Metadata
  prefabData._derivedName = "abab - 001"
  prefabData._derivedPath = "003/abab - 001"

Step 5: Save Prefab File
  savePrefabFile(prefabData, output, "a")
    derivedSubdir = path.dirname("003/abab - 001") = "003"
    dir = path.join("output", "assets", "a", "003")
    → Creates: output/assets/a/003/abab - 001.prefab ✓
```

## Verification
Config analysis shows:
- Bundle "a" declares: `"3": ["003/abab - 001", 0]`
- UUID[3] = `4fyraXpfdGZYZ9t+2ao7YI` 
- Path[3] = `003/abab - 001`
- Import version: index 3 → hash `83dee`

With these changes:
- ✓ File will be discovered via importHash → UUID mapping
- ✓ UUID will resolve to correct path with subdirectory
- ✓ Subdirectory will be extracted and used in output path
- ✓ File saved to correct location: `assets/a/003/abab - 001.prefab`

## Testing Recommendations
1. Run reversal on test project: `2026/web-mobile` (compiled output)
2. Verify output structure:
   - `assets/a/003/` directory exists
   - `assets/a/003/abab - 001.prefab` file exists (not in `a/`)
3. Check verbose logs for routing decisions
4. Compare with bundle config paths

## Backward Compatibility
- ✓ Changes are additive (new lookup path, not replacing existing logic)
- ✓ Fallback chain ensures files still save if mapping fails
- ✓ Existing functionality for non-prefab assets unchanged
