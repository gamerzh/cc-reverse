#!/usr/bin/env python3
"""
集成测试：验证逆向工具是否能正确处理TypeScript文件
"""

import os
import sys
import shutil
import tempfile

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.reverseEngine import reverseProject
from utils.logger import logger

def test_reverse_with_ts_files():
    """测试逆向工具处理包含TypeScript文件的项目"""
    
    # 配置日志
    logger().set_level("debug")
    
    # 使用用户的实际项目路径（只读访问）
    source_path = r"C:\Workflow\xsh5"
    if not os.path.exists(source_path):
        print(f"源路径不存在: {source_path}")
        print("请确保项目路径正确")
        return False
    
    # 创建临时输出目录
    temp_dir = tempfile.mkdtemp(prefix='_reccverse_test_')
    output_path = os.path.join(temp_dir, 'output')
    
    print(f"测试源路径: {source_path}")
    print(f"测试输出路径: {output_path}")
    
    try:
        # 配置逆向选项
        options = {
            'sourcePath': source_path,
            'outputPath': output_path,
            'verbose': True,
            'silent': False,
            'versionHint': ''  # 自动检测
        }
        
        print("\n开始逆向工程测试...")
        success = reverseProject(options)
        
        if not success:
            print("❌ 逆向工程失败")
            return False
        
        print("\n✅ 逆向工程完成")
        
        # 检查输出目录结构
        print("\n检查输出目录结构...")
        
        # 检查fhpoker目录是否存在
        fhpoker_output = os.path.join(output_path, 'assets', 'fhpoker')
        if os.path.exists(fhpoker_output):
            print(f"✅ fhpoker目录存在: {fhpoker_output}")
            
            # 列出所有子目录
            expected_folders = ['animation', 'effect', 'prefabs', 'scenes', 'script', 'sound', 'textures']
            for folder in expected_folders:
                folder_path = os.path.join(fhpoker_output, folder)
                if os.path.exists(folder_path):
                    print(f" ✅  {folder}文件夹存在")
                    # 如果是script文件夹，检查.ts文件
                    if folder == 'script':
                        ts_files = []
                        for root, _, files in os.walk(folder_path):
                            for file in files:
                                if file.endswith('.ts'):
                                    ts_files.append(os.path.relpath(os.path.join(root, file), folder_path))
                        if ts_files:
                            print(f"    找到 {len(ts_files)} 个.ts文件:")
                            for ts_file in ts_files[:10]:  # 最多显示10个
                                print(f"      📄 {ts_file}")
                            if len(ts_files) > 10:
                                print(f"      ... 还有 {len(ts_files) - 10} 个")
                        else:
                            print(f"    ❌ script文件夹中没有.ts文件")
                else:
                    print(f"  ❌ {folder}文件夹缺失")
        else:
            print(f"❌ fhpoker目录不存在: {fhpoker_output}")
        
        # 检查scripts目录（codeAnalyzer生成）
        scripts_dir = os.path.join(output_path, 'assets', 'scripts')
        if os.path.exists(scripts_dir):
            print(f"\n📁 scripts目录存在: {scripts_dir}")
            ts_files = [f for f in os.listdir(scripts_dir) if f.endswith('.ts')]
            if ts_files:
                print(f"  包含 {len(ts_files)} 个生成的.ts文件")
            else:
                print(f"  不包含.ts文件（可能被禁用了）")
        
        # 统计总文件数
        print("\n📊 输出目录统计:")
        total_files = 0
        ts_files_count = 0
        for root, _, files in os.walk(output_path):
            total_files += len(files)
            ts_files_count += sum(1 for f in files if f.endswith('.ts'))
        
        print(f"  总文件数: {total_files}")
        print(f"  TypeScript文件数: {ts_files_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理临时目录
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"\n已清理临时目录: {temp_dir}")

if __name__ == '__main__':
    print("=" * 60)
    print("Cocos Creator逆向工具集成测试")
    print("=" * 60)
    
    # 先检查项目结构
    source_path = r"C:\Workflow\xsh5"
    if os.path.exists(source_path):
        print(f"检查项目结构: {source_path}")
        
        # 检查fhpoker目录
        fhpoker_source = os.path.join(source_path, 'assets', 'res', 'fhpoker')
        if os.path.exists(fhpoker_source):
            print(f"✅ 找到原始fhpoker目录: {fhpoker_source}")
            
            # 检查script文件夹
            script_source = os.path.join(fhpoker_source, 'script')
            if os.path.exists(script_source):
                print(f"✅ 找到原始script文件夹")
                # 统计.ts文件
                ts_files = []
                for root, _, files in os.walk(script_source):
                    ts_files.extend([os.path.join(root, f) for f in files if f.endswith('.ts')])
                print(f"  包含 {len(ts_files)} 个原始.ts文件")
                if ts_files:
                    print(f"  示例文件: {os.path.basename(ts_files[0])}")
            else:
                print(f"❌ 原始script文件夹不存在")
        else:
            print(f"❌ 原始fhpoker目录不存在")
    
    print("\n" + "=" * 60)
    
    # 运行测试
    success = test_reverse_with_ts_files()
    
    if success:
        print("\n✅ 测试完成")
    else:
        print("\n❌ 测试失败")