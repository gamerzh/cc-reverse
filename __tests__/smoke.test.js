const fs = require('fs');
const fsp = fs.promises;
const path = require('path');
const os = require('os');

const { reverseProject } = require('../src/core/reverseEngine');

jest.setTimeout(30000);

async function createTempDir(prefix) {
  const dir = await fsp.mkdtemp(path.join(os.tmpdir(), prefix));
  return dir;
}

async function write(filePath, content) {
  await fsp.mkdir(path.dirname(filePath), { recursive: true });
  await fsp.writeFile(filePath, content, 'utf8');
}

async function fileExists(p) {
  try {
    await fsp.access(p, fs.constants.F_OK);
    return true;
  } catch (e) {
    return false;
  }
}

// Minimal settings.js that our AST parser can read safely
function minimalSettingsContent() {
  return [
    'window._CCSettings = {',
    '  bundleVers: {},',
    '  uuids: {},',
    '  subpackages: {},',
    '  launchScene: "db://assets/Scene/Main.fire"',
    '};'
  ].join('\n');
}

// Settings with rawAssets for name derivation
function settingsWithRawAssets(rawAssetsSnippet) {
  return [
    'window._CCSettings = {',
    '  bundleVers: {},',
    '  uuids: {},',
    '  subpackages: {},',
    '  launchScene: "db://assets/Scene/Main.fire",',
    `  rawAssets: ${rawAssetsSnippet}`,
    '};'
  ].join('\n');
}

describe('cc-reverse smoke', () => {
  test('runs reverseProject on minimal 2.3.x layout', async () => {
    const src = await createTempDir('cc-rev-src-');
    const out = await createTempDir('cc-rev-out-');

    // Create 2.3.x style structure
    await write(path.join(src, 'src', 'settings.js'), minimalSettingsContent());
    await write(path.join(src, 'src', 'project.js'), 'console.log("project");');
    await write(path.join(src, 'res', 'placeholder.txt'), 'res');

    // Add a dummy bundle file
    await write(path.join(src, 'bundles', 'main', 'index.deadbeef.js'), 'var x = 1;');

    const ok = await reverseProject({
      sourcePath: src,
      outputPath: out,
      verbose: true,
      versionHint: '2.3.x',
      bundleConcurrency: 1
    });

    expect(ok).toBeTruthy();
    // Check essential outputs
    expect(await fileExists(path.join(out, 'project.json'))).toBe(true);
    expect(await fileExists(path.join(out, 'settings', 'project.json'))).toBe(true);
  });

  test('supports bundle concurrency and original structure option', async () => {
    const src = await createTempDir('cc-rev-src-');
    const out = await createTempDir('cc-rev-out-');
    const orig = await createTempDir('cc-rev-orig-');

    // Pretend original structure has some folders
    await fsp.mkdir(path.join(orig, 'assets', 'res'), { recursive: true });

    // Minimal project
    await write(path.join(src, 'src', 'settings.js'), minimalSettingsContent());
    await write(path.join(src, 'src', 'project.js'), 'console.log("project");');
    await write(path.join(src, 'res', 'placeholder.txt'), 'res');

    // Multiple bundle files to exercise concurrency
    await write(path.join(src, 'bundles', 'a', 'index.aaa111.js'), 'var a = 1;');
    await write(path.join(src, 'bundles', 'b', 'index.bbb222.js'), 'var b = 2;');

    const ok = await reverseProject({
      sourcePath: src,
      outputPath: out,
      verbose: true,
      originalStructure: path.join(orig, 'assets', 'res'),
      versionHint: '2.3.x',
      bundleConcurrency: 2
    });

    expect(ok).toBeTruthy();
    expect(await fileExists(path.join(out, 'project.json'))).toBe(true);
  });

  test('generates prefab file from import JSON', async () => {
    const src = await createTempDir('cc-rev-src-');
    const out = await createTempDir('cc-rev-out-');

    // Minimal project
    await write(path.join(src, 'src', 'settings.js'), minimalSettingsContent());
    await write(path.join(src, 'src', 'project.js'), 'console.log("project");');
    // Minimal import prefab JSON
    await write(path.join(src, 'res', 'import', 'prefabs', 'my_prefab.json'), JSON.stringify([
      1,        // version
      [],       // uuids
      [],       // names
      ['cc.Prefab'], // types
      [],       // typeIndices
      [],       // objects
      [],       // assets
      [],       // depends
      'db://assets/prefabs/my_prefab.prefab', // exportPath
      false     // isScene
    ]));

    const ok = await reverseProject({
      sourcePath: src,
      outputPath: out,
      verbose: true,
      versionHint: '2.3.x',
      bundleConcurrency: 1
    });

    expect(ok).toBeTruthy();
    const prefabPath = path.join(out, 'assets', 'common', 'prefabs', 'my_prefab.prefab');
    expect(await fileExists(prefabPath)).toBe(true);
  });

  test('generates scene file from import JSON', async () => {
    const src = await createTempDir('cc-rev-src-');
    const out = await createTempDir('cc-rev-out-');

    await write(path.join(src, 'src', 'settings.js'), minimalSettingsContent());
    await write(path.join(src, 'src', 'project.js'), 'console.log("project");');
    // Minimal import scene JSON per parser expectations
    await write(path.join(src, 'res', 'import', 'scenes', 'my_scene.json'), JSON.stringify([
      1,        // version
      [],       // uuids
      [],       // names
      ['cc.SceneAsset'], // types
      [],       // typeIndices
      [],       // objects
      [],       // assets
      [],       // depends
      'db://assets/scenes/my_scene.fire', // exportPath
      true      // isScene
    ]));

    const ok = await reverseProject({
      sourcePath: src,
      outputPath: out,
      verbose: true,
      versionHint: '2.3.x',
      bundleConcurrency: 1
    });

    expect(ok).toBeTruthy();
    const scenePath = path.join(out, 'assets', 'common', 'scenes', 'my_scene.fire');
    const sceneMetaPath = scenePath + '.meta';
    expect(await fileExists(scenePath)).toBe(true);
    expect(await fileExists(sceneMetaPath)).toBe(true);
  });

  test('processes sprite atlas JSON and writes plist output', async () => {
    const src = await createTempDir('cc-rev-src-');
    const out = await createTempDir('cc-rev-out-');

    await write(path.join(src, 'src', 'settings.js'), minimalSettingsContent());
    await write(path.join(src, 'src', 'project.js'), 'console.log("project");');
    // Minimal import sprite atlas JSON; objects can be empty for this smoke
    await write(path.join(src, 'res', 'import', 'atlases', 'my_atlas.json'), JSON.stringify([
      1,        // version
      [],       // uuids
      [],       // names
      ['cc.SpriteAtlas'], // types
      [],       // typeIndices
      [],       // objects
      [],       // assets
      [],       // depends
      'db://assets/atlases/my_atlas', // exportPath (no extension in this minimal case)
      false     // isScene
    ]));

    const ok = await reverseProject({
      sourcePath: src,
      outputPath: out,
      verbose: true,
      versionHint: '2.3.x',
      bundleConcurrency: 1
    });

    expect(ok).toBeTruthy();
    // Assert that a plist file is written
    const plistPath = path.join(out, 'assets', 'common', 'textures', 'my_atlas.plist');
    const metaPath = plistPath + '.meta';
    expect(await fileExists(plistPath)).toBe(true);
    expect(await fileExists(metaPath)).toBe(true);
  });

  test('prefab name falls back to names[] when exportPath missing', async () => {
    const src = await createTempDir('cc-rev-src-');
    const out = await createTempDir('cc-rev-out-');

    await write(path.join(src, 'src', 'settings.js'), minimalSettingsContent());
    await write(path.join(src, 'src', 'project.js'), 'console.log("project");');

    // Import prefab JSON without exportPath; provide names[] with a readable name
    await write(path.join(src, 'res', 'import', 'prefabs', 'abcd1234.json'), JSON.stringify([
      1,                // version
      [],               // uuids
      ['ReadablePrefab.prefab'], // names (fallback)
      ['cc.Prefab'],    // types
      [],               // typeIndices
      [],               // objects
      [],               // assets
      [],               // depends
      '',               // exportPath missing/empty
      false             // isScene
    ]));

    const ok = await reverseProject({
      sourcePath: src,
      outputPath: out,
      verbose: true,
      versionHint: '2.3.x',
      bundleConcurrency: 1
    });

    expect(ok).toBeTruthy();
    const prefabPath = path.join(out, 'assets', 'common', 'prefabs', 'ReadablePrefab.prefab');
    expect(await fileExists(prefabPath)).toBe(true);
  });

  test('prefab name can be derived deep from data when exportPath and names[] are missing', async () => {
    const src = await createTempDir('cc-rev-src-');
    const out = await createTempDir('cc-rev-out-');

    await write(path.join(src, 'src', 'settings.js'), minimalSettingsContent());
    await write(path.join(src, 'src', 'project.js'), 'console.log("project");');

    // No exportPath, empty names; embed a path-like string somewhere deep (in assets array)
    await write(path.join(src, 'res', 'import', 'prefabs', 'no_names.json'), JSON.stringify([
      1,                // version
      [],               // uuids
      [],               // names
      ['cc.Prefab'],    // types
      [],               // typeIndices
      [],               // objects
      ["db://assets/prefabs/DeepDerived.prefab"], // assets carries a hint
      [],               // depends
      '',               // exportPath missing
      false             // isScene
    ]));

    const ok = await reverseProject({
      sourcePath: src,
      outputPath: out,
      verbose: true,
      versionHint: '2.3.x',
      bundleConcurrency: 1
    });

    expect(ok).toBeTruthy();
    const prefabPath = path.join(out, 'assets', 'common', 'prefabs', 'DeepDerived.prefab');
    expect(await fileExists(prefabPath)).toBe(true);
  });

  test('prefab name derived from rawAssets when exportPath/names[] missing', async () => {
    const src = await createTempDir('cc-rev-src-');
    const out = await createTempDir('cc-rev-out-');

    // Settings include rawAssets.assets mapping uuid to path
    const settings = settingsWithRawAssets(JSON.stringify({
      assets: {
        "uuid-raw-1": ["prefabs/FromRawAssets", "cc.Prefab", 1]
      }
    }));
    await write(path.join(src, 'src', 'settings.js'), settings);
    await write(path.join(src, 'src', 'project.js'), 'console.log("project");');

    // Serialized data with uuids referencing rawAssets key, but no exportPath/names
    await write(path.join(src, 'res', 'import', 'prefabs', 'from_raw.json'), JSON.stringify([
      1,                // version
      ['uuid-raw-1'],   // uuids
      [],               // names
      ['cc.Prefab'],    // types
      [],               // typeIndices
      [],               // objects
      [],               // assets
      [],               // depends
      '',               // exportPath missing
      false             // isScene
    ]));

    const ok = await reverseProject({
      sourcePath: src,
      outputPath: out,
      verbose: true,
      versionHint: '2.3.x',
      bundleConcurrency: 1
    });

    expect(ok).toBeTruthy();
    const prefabPath = path.join(out, 'assets', 'common', 'prefabs', 'FromRawAssets.prefab');
    expect(await fileExists(prefabPath)).toBe(true);
  });

  test('prefab name derived from originalStructure when uuid matches meta', async () => {
    const src = await createTempDir('cc-rev-src-');
    const out = await createTempDir('cc-rev-out-');
    const orig = await createTempDir('cc-rev-orig-');

    const uuid = 'uuid-orig-1';
    const origRoot = path.join(orig, 'assets', 'res');
    const origPrefabDir = path.join(origRoot, 'fhpoker', 'prefabs');
    await write(path.join(origPrefabDir, 'Pretty.prefab'), 'prefab');
    await write(path.join(origPrefabDir, 'Pretty.prefab.meta'), JSON.stringify({ uuid }));

    await write(path.join(src, 'src', 'settings.js'), minimalSettingsContent());
    await write(path.join(src, 'src', 'project.js'), 'console.log("project");');

    // Import prefab JSON without exportPath/names/rawAssets; uuids matches original meta
    await write(path.join(src, 'res', 'import', 'prefabs', 'hashed.json'), JSON.stringify([
      1,                // version
      [uuid],           // uuids
      [],               // names
      ['cc.Prefab'],    // types
      [],               // typeIndices
      [],               // objects
      [],               // assets
      [],               // depends
      '',               // exportPath missing
      false             // isScene
    ]));

    const ok = await reverseProject({
      sourcePath: src,
      outputPath: out,
      verbose: true,
      originalStructure: origRoot,
      versionHint: '2.3.x',
      bundleConcurrency: 1
    });

    expect(ok).toBeTruthy();
    const prefabPath = path.join(out, 'assets', 'common', 'prefabs', 'Pretty.prefab');
    expect(await fileExists(prefabPath)).toBe(true);
  });

  test('non-array serialized JSON is skipped without throwing', async () => {
    const src = await createTempDir('cc-rev-src-');
    const out = await createTempDir('cc-rev-out-');

    await write(path.join(src, 'src', 'settings.js'), minimalSettingsContent());
    await write(path.join(src, 'src', 'project.js'), 'console.log("project");');

    // Malformed: root is object, not array
    await write(path.join(src, 'res', 'import', 'prefabs', 'bad.json'), JSON.stringify({ foo: 'bar' }));

    const ok = await reverseProject({
      sourcePath: src,
      outputPath: out,
      verbose: true,
      versionHint: '2.3.x',
      bundleConcurrency: 1
    });

    expect(ok).toBeTruthy();
    // Should not create a prefab
    const prefabPath = path.join(out, 'assets', 'common', 'prefabs', 'bad.prefab');
    expect(await fileExists(prefabPath)).toBe(false);
  });
});
