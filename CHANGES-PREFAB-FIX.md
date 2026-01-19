# Fix: Correct Prefab File Placement in Bundle Subdirectories

## Problem
Prefab files were being placed in bundle root directory (e.g., `a/abab - 001.prefab`) instead of their correct subdirectories (e.g., `a/003/abab - 001.prefab`), even though the bundle config correctly declared the paths (e.g., `"003/abab - 001"`).

## Root Cause
The `processSerializedFile()` method, which handles prefab files from the import directory, was not using the UUID-to-path mapping to determine the correct subdirectory. It lacked the logic to:
1. Look up the UUID of a resource in the `uuidPathMap`
2. Extract the subdirectory information from the mapped path
3. Pass this subdirectory information to `savePrefabFile()`

## Solution
Enhanced `processSerializedFile()` to:

1. **Retrieve the UUID** from import file through `importHashToUuid` map
2. **Look up in uuidPathMap** - NEW: Use the UUID to directly query the `uuidPathMap` which contains UUID → path mappings from bundle config
3. **Extract subdirectory** - If found, use the path's directory component as subdirectory
4. **Fallback chain** - If uuidPathMap fails, try importHashToPath, then bundlePathsMap
5. **Pass metadata** - Set `_derivedPath` on prefabData before saving

## Files Modified
- `src/core/resourceProcessor.js`
  - `processSerializedFile()`: Added uuidPathMap lookup and improved fallback chain
  - Added debug logging for file routing decisions
  
- `src/core/serializationParser.js`
  - `savePrefabFile()`: Added debug logging when _derivedPath is provided

## Testing
Verified through config analysis that:
- Bundle config contains: `"3": ["003/abab - 001", 0]`
- UUID[3] = `4fyraXpfdGZYZ9t+2ao7YI` maps to path `003/abab - 001`
- Import version mapping: index 3 → hash `83dee`
- With the fix, files will be saved to: `assets/a/003/abab - 001.prefab`

## Example Flow
```
Import file: 83dee.xxx.json
  → importHashToUuid.get("83dee") → { uuid: "4fyraXpfdGZYZ9t+2ao7YI" }
  → uuidPathMap.get("4fyraXpfdGZYZ9t+2ao7YI") → { path: "003/abab - 001" }
  → derivedPath = "003/abab - 001"
  → savePrefabFile() extracts subdir: dirname("003/abab - 001") = "003"
  → Final output: assets/a/003/abab - 001.prefab ✓
```
