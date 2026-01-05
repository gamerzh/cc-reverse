#!/usr/bin/env python3
"""
调试脚本文件夹缺失问题
"""

import os
import sys
import shutil
import tempfile

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.resourceProcessor import ResourceProcessor

def test_script_folder():
    # 创建临时目录
    test_dir = tempfile.mkdtemp(prefix='cc_reverse_test_')
    source_dir = os.path.join(test_dir, 'source')
    output_dir = os.path.join(test_dir, 'output')
    
    # 创建模拟的fhpoker目录结构，模仿原始工程
    fhpoker_dir = os.path.join(source_dir, 'assets', 'res', 'fhpoker')
    os.makedirs(os.path.join(fhpoker_dir, 'script', 'liukou', 'manager'))
    os.makedirs(os.path.join(fhpoker_dir, 'script', 'mingkou', 'manager'))
    os.makedirs(os.path.join(fhpoker_dir, 'animation'))
    os.makedirs(os.path.join(fhpoker_dir, 'effect', 'shalou'))
    os.makedirs(os.path.join(fhpoker_dir, 'prefabs', 'view'))
    os.makedirs(os.path.join(fhpoker_dir, 'scenes'))
    os.makedirs(os.path.join(fhpoker_dir, 'sound'))
    os.makedirs(os.path.join(fhpoker_dir, 'textures', 'image'))
    
    # 创建一些测试文件
    with open(os.path.join(fhpoker_dir, 'script', 'liukou', 'manager', 'fhlkGameDatamanager.ts'), 'w') as f:
        f.write('// TypeScript file')
    
    with open(os.path.join(fhpoker_dir, 'script', 'mingkou', 'FHMKGameScene.ts'), 'w') as f:
        f.write('// TypeScript file')
    
    with open(os.path.join(fhpoker_dir, 'animation', 'FHMKStartAni.anim'), 'w') as f:
        f.write('{}')
    
    with open(os.path.join(fhpoker_dir, 'effect', 'shalou', 'shalou.anim'), 'w') as f:
        f.write('{}')
    
    with open(os.path.join(fhpoker_dir, 'prefabs', 'view', 'FHPokerMenuView.prefab'), 'w') as f:
        f.write('{}')
    
    with open(os.path.join(fhpoker_dir, 'scenes', 'FHMKScene.fire'), 'w') as f:
        f.write('{}')
    
    with open(os.path.join(fhpoker_dir, 'sound', 'clock.wav'), 'wb') as f:
        f.write(b'fake wav data')
    
    with open(os.path.join(fhpoker_dir, 'textures', 'image', 'test.png'), 'wb') as f:
        f.write(b'PNG data')
    
    # 创建一个模拟的config.json文件（编译后的资源配置）
    config_dir = os.path.join(source_dir, 'assets', 'res', 'fhpoker')
    with open(os.path.join(config_dir, 'config.123.json'), 'w') as f:
        f.write('{"types": ["cc.Prefab", "cc.Scene"], "paths": {"0": ["prefabs/view/FHPokerMenuView.prefab"]}, "uuids": ["uuid-123"]}')
    
    print("创建的源目录结构:")
    for root, dirs, files in os.walk(source_dir):
        level = root.replace(source_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")
    
    # 初始化资源处理器
    resource_processor = ResourceProcessor()
    
    # 准备路径字典（模拟逆向工具的路径）
    paths = {
        'source': source_dir,
        'output': output_dir,
        'res': os.path.join(source_dir, 'assets', 'res')
    }
    
    print(f"\n资源处理器使用的路径:")
    print(f"  source: {paths['source']}")
    print(f"  output: {paths['output']}")
    print(f"  res: {paths['res']}")
    
    # 运行资源处理
    print("\n开始资源处理...")
    resource_processor.processResources(paths)
    
    print("\n输出目录结构:")
    for root, dirs, files in os.walk(output_dir):
        level = root.replace(output_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")
    
    # 检查script文件夹是否被创建
    script_output_path = os.path.join(output_dir, 'assets', 'fhpoker', 'script')
    if os.path.exists(script_output_path):
        print(f"\n✅ script文件夹已创建: {script_output_path}")
        ts_files = []
        for root, _, files in os.walk(script_output_path):
            for file in files:
                if file.endswith('.ts'):
                    ts_files.append(os.path.join(root, file))
        print(f"   找到 {len(ts_files)} 个.ts文件")
    else:
        print(f"\n❌ script文件夹未创建")
        print(f"  期望路径: {script_output_path}")
    
    # 检查其他文件夹
    expected_folders = ['animation', 'effect', 'prefabs', 'scenes', 'script', 'sound', 'textures']
    for folder in expected_folders:
        folder_path = os.path.join(output_dir, 'assets', 'fhpoker', folder)
        if os.path.exists(folder_path):
            print(f"✅ {folder}文件夹存在")
        else:
            print(f"❌ {folder}文件夹缺失")
    
    # 清理
    shutil.rmtree(test_dir)
    print(f"\n测试完成，已清理临时目录: {test_dir}")

if __name__ == '__main__':
    test_script_folder()