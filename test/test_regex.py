#!/usr/bin/env python3
import re

# 测试代码片段（从ChangeTool.js提取）
test_code = '''c=function(e){function t(){return null!==e&&e.apply(this,arguments)||this}return n(t,e),t.prototype.onLoad=function(){var e=this;this.node.getChildByName("items").children.forEach(function(t,o){var a=48+o+1;t.on(cc.Node.EventType.TOUCH_END,e._onChange.bind(e,a),e),t.getComponent(r.FHPokerItem).setCardValue(a)})},t.prototype.start=function(){},t.prototype._onChange=function(e){this._target&&(this._target.changeValue=e),this.node.active=!1},Object.defineProperty(t.prototype,"target",{set:function(e){this._target=e},enumerable:!1,configurable:!0}),t.prototype.onDisable=function(){this._target=null},i([s],t)}(cc.Component)'''

print("原始代码片段:")
print(test_code[:200] + "...")
print("\n" + "="*80 + "\n")

# 测试各种正则表达式模式
patterns = [
    # 模式1：匹配 function(e){function t(){...}n(t,e);...}i([s],t)}(cc.Component)
    r'function\s*\((\w+)\)\s*\{[^}]*?function\s+(\w+)[^}]*?n\(\2,\s*\1\)[^}]*?\}\s*i\(\[([^\]]+)\],\s*\2\)\}\(([^)]+)\)',
    
    # 模式2：简化版本，不要求严格的n(t,e)顺序
    r'function\s*\((\w+)\)\s*\{[^}]*?function\s+(\w+)[^}]*?n\([^)]*\)[^}]*?\}\s*i\(\[([^\]]+)\],\s*\2\)\}\(([^)]+)\)',
    
    # 模式3：更宽松的匹配
    r'function\s*\((\w+)\)\s*\{[^}]*?function\s+(\w+)[^}]*?\}\s*i\(\[([^\]]+)\],\s*\2\)\}\(([^)]+)\)',
    
    # 模式4：查找任何类定义模式
    r'(\w+)=function\s*\((\w+)\)\s*\{[^}]*?function\s+(\w+)[^}]*?\}[^}]+\}\(([^)]+)\)',
    
    # 模式5：查找包含i([...],t)的模式
    r'i\(\[([^\]]+)\],\s*(\w+)\)\}\(([^)]+)\)',
]

for i, pattern in enumerate(patterns):
    print(f"\n模式{i+1}: {pattern}")
    try:
        match = re.search(pattern, test_code, re.DOTALL)
        if match:
            print(f"  匹配成功!")
            print(f"  组数: {len(match.groups())}")
            for j, group in enumerate(match.groups()):
                if group:
                    print(f"  组{j+1}: {group[:50]}{'...' if len(group) > 50 else ''}")
        else:
            print(f"  无匹配")
    except Exception as e:
        print(f"  错误: {e}")

print("\n" + "="*80 + "\n")
print("尝试提取所有可能的类定义模式...")

# 查找所有可能包含类定义的片段
class_keywords = [
    'function(',
    'n(',
    'i([',
    'prototype',
    'Object.defineProperty'
]

for keyword in class_keywords:
    idx = test_code.find(keyword)
    if idx != -1:
        print(f"\n找到 '{keyword}' 在位置 {idx}")
        # 显示上下文
        start = max(0, idx - 50)
        end = min(len(test_code), idx + 100)
        print(f"  上下文: ...{test_code[start:end]}...")