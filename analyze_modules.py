#!/usr/bin/env python3
"""
分析从bundle中提取的模块代码，识别TypeScript类定义
"""

import os
import re
import json

def analyze_module(file_path):
    """分析单个模块文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"\n分析文件: {os.path.basename(file_path)}")
    print("-" * 80)
    
    # 1. 查找类名 (在 cc._RF.push 中)
    rf_pattern = r'cc\._RF\.push\(t,\s*"[^"]+",\s*"([^"]+)"\)'
    rf_match = re.search(rf_pattern, content)
    if rf_match:
        class_name = rf_match.group(1)
        print(f"类名: {class_name}")
    else:
        # 尝试从导出中查找
        export_pattern = r'o\.(\w+)=[mt],'
        export_match = re.search(export_pattern, content)
        if export_match:
            class_name = export_match.group(1)
            print(f"导出名: {class_name}")
        else:
            class_name = None
    
    # 2. 查找继承关系 (查找 extends 或 __extends)
    # 模式: var m = function(e) { function t() { ... } n(t,e); ... }
    extends_pattern = r'n\(t,\s*e\)'
    if re.search(extends_pattern, content):
        # 查找父类参数 (在 function(e) 中)
        parent_pattern = r'function\s*\(\s*(\w+)\s*\)'
        parent_match = re.search(parent_pattern, content)
        if parent_match:
            parent_var = parent_match.group(1)
            # 查找父类变量对应的实际类名
            # 模式: var r = e("../../../scripts/ui/UIPopup")
            import_pattern = rf'var\s+{parent_var}\s*=\s*e\("([^"]+)"\)'
            import_match = re.search(import_pattern, content)
            if import_match:
                import_path = import_match.group(1)
                print(f"继承自: {import_path}")
    
    # 3. 查找装饰器属性
    # 模式: i([p(cc.Node)], t.prototype, "close_btn", void 0)
    decorator_pattern = r'i\(\[([^]]+)\],\s*t\.prototype,\s*"([^"]+)"[^)]*\)'
    decorator_matches = re.findall(decorator_pattern, content)
    if decorator_matches:
        print(f"装饰器属性 ({len(decorator_matches)} 个):")
        for decorator, prop_name in decorator_matches:
            # 解析装饰器类型
            if 'p(' in decorator:
                # @property 装饰器
                prop_type_match = re.search(r'p\(([^)]+)\)', decorator)
                if prop_type_match:
                    prop_type = prop_type_match.group(1)
                    print(f"  @property({prop_type}) {prop_name}")
            elif 'u' in decorator:
                print(f"  @ccclass {prop_name}")
    
    # 4. 查找方法
    # 模式: t.prototype.methodName = function(...) { ... }
    method_pattern = r't\.prototype\.(\w+)\s*=\s*function\s*\(([^)]*)\)\s*\{'
    method_matches = re.findall(method_pattern, content)
    if method_matches:
        print(f"方法 ({len(method_matches)} 个):")
        for method_name, params in method_matches:
            print(f"  {method_name}({params})")
    
    # 5. 查找cc.Class定义 (可能存在于某些模块中)
    class_patterns = [
        r'cc\.Class\s*\(\s*\{([\s\S]*?)\}\s*\)',
        r'\w\.Class\s*\(\s*\{([\s\S]*?)\}\s*\)',
        r'\w\["Class"\]\s*\(\s*\{([\s\S]*?)\}\s*\)',
        r"\w\['Class'\]\s*\(\s*\{([\s\S]*?)\}\s*\)",
    ]
    
    for pattern in class_patterns:
        class_matches = re.findall(pattern, content)
        if class_matches:
            print(f"找到cc.Class定义 ({len(class_matches)} 个)")
            for i, class_body in enumerate(class_matches[:1]):  # 只显示第一个
                print(f"  类体片段: {class_body[:200]}...")
    
    return class_name

def main():
    """主函数"""
    extracted_dir = "extracted_fhpoker"
    if not os.path.exists(extracted_dir):
        print(f"目录不存在: {extracted_dir}")
        return
    
    files = [f for f in os.listdir(extracted_dir) if f.endswith('.js')]
    print(f"找到 {len(files)} 个模块文件")
    
    class_names = []
    for i, filename in enumerate(files[:10]):  # 只分析前10个
        file_path = os.path.join(extracted_dir, filename)
        class_name = analyze_module(file_path)
        if class_name:
            class_names.append(class_name)
    
    print(f"\n总结: 识别到 {len(class_names)} 个类")
    for name in class_names:
        print(f"  - {name}")

if __name__ == "__main__":
    main()