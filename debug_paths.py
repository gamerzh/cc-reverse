#!/usr/bin/env python3
"""
调试逆向工具路径检测
"""

import os
import sys

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.reverseEngine import detectProjectVersion
from utils.logger import logger

# 配置日志
logger().set_level("info")

# 测试源路径
source_path = r"C:\Workflow\xsh5"
print(f"检测源路径: {source_path}")

try:
    project_info = detectProjectVersion(source_path, "")
    print(f"检测到的项目信息:")
    print(f"  版本: {project_info['version']}")
    print(f"  设置文件路径: {project_info['settingsPath']}")
    print(f"  项目文件路径: {project_info['projectPath']}")
    print(f"  资源路径 (resPath): {project_info['resPath']}")
    
    # 检查资源路径是否存在
    if os.path.exists(project_info['resPath']):
        print(f"  资源路径存在")
        # 列出资源路径下的内容
        items = os.listdir(project_info['resPath'])
        print(f"  资源路径下的项目 ({len(items)} 个):")
        for item in items[:20]:  # 最多显示20个
            item_path = os.path.join(project_info['resPath'], item)
            if os.path.isdir(item_path):
                print(f"    📁 {item}/")
            else:
                print(f"    📄 {item}")
        if len(items) > 20:
            print(f"    ... 还有 {len(items) - 20} 个")
    else:
        print(f"  资源路径不存在！")
        
    # 检查fhpoker目录是否存在
    fhpoker_path = os.path.join(project_info['resPath'], 'fhpoker')
    if os.path.exists(fhpoker_path):
        print(f"\n找到fhpoker目录: {fhpoker_path}")
        print(f"fhpoker目录下的子目录:")
        for item in os.listdir(fhpoker_path):
            item_path = os.path.join(fhpoker_path, item)
            if os.path.isdir(item_path):
                print(f"  📁 {item}/")
                # 列出该子目录中的文件数量
                sub_items = os.listdir(item_path)
                file_count = sum(1 for subitem in sub_items if os.path.isfile(os.path.join(item_path, subitem)))
                dir_count = len(sub_items) - file_count
                print(f"      {len(sub_items)} 个项目 ({file_count} 个文件, {dir_count} 个目录)")
    else:
        print(f"\n未找到fhpoker目录")
        
except Exception as e:
    print(f"检测失败: {e}")
    import traceback
    traceback.print_exc()