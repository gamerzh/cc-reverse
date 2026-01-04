#!/usr/bin/env python3
import os
import re

def find_scenes_in_settings(source_path):
    # 查找settings文件
    settings_files = []
    for root, dirs, files in os.walk(source_path):
        for file in files:
            if file.startswith('settings') and file.endswith('.js'):
                settings_files.append(os.path.join(root, file))
    
    print(f"找到 {len(settings_files)} 个settings文件")
    
    # 分析每个settings文件
    for settings_file in settings_files:
        print(f"\n分析文件: {settings_file}")
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找场景配置
            scene_config = re.search(r'(?:scene|Scene).*?:.*?\[(.*?)\]', content, re.DOTALL)
            if scene_config:
                print(f"场景配置: {scene_config.group(1)}")
            
            # 查找CCSettings配置
            ccsettings_match = re.search(r'window\._CCSettings\s*=\s*({[^;]+});', content, re.DOTALL)
            if ccsettings_match:
                print("找到CCSettings配置")
                # 提取scenes配置
                scenes_match = re.search(r'scenes\s*:\s*\[(.*?)\]', ccsettings_match.group(1), re.DOTALL)
                if scenes_match:
                    print(f"CCSettings场景配置: {scenes_match.group(1)}")
            
        except Exception as e:
            print(f"分析文件 {settings_file} 失败: {e}")

if __name__ == "__main__":
    source_path = "C:/Workflow/xsh5/build/web-mobile"
    find_scenes_in_settings(source_path)
