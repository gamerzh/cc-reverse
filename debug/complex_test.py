#!/usr/bin/env python3
"""
创建更复杂的测试项目，模拟真实的Cocos Creator Web编译输出
"""

import os
import shutil

# 测试项目路径
test_project_path = "complex_test_project"
test_output_path = "complex_test_output"

# 创建目录结构
def create_complex_project():
    """创建复杂测试项目"""
    print("创建复杂测试项目...")
    
    # 清理旧项目
    if os.path.exists(test_project_path):
        shutil.rmtree(test_project_path)
    
    # 创建基本目录
    os.makedirs(os.path.join(test_project_path, "src"), exist_ok=True)
    os.makedirs(os.path.join(test_project_path, "assets"), exist_ok=True)
    os.makedirs(os.path.join(test_project_path, "assets", "scripts"), exist_ok=True)
    os.makedirs(os.path.join(test_project_path, "assets", "textures"), exist_ok=True)
    os.makedirs(os.path.join(test_project_path, "assets", "sounds"), exist_ok=True)
    
    # 创建settings.js
    create_settings_file()
    
    # 创建main.js
    create_main_file()
    
    # 创建多个组件
    create_components()
    
    # 创建资源文件
    create_assets()
    
    print("复杂测试项目创建完成！")

def create_settings_file():
    """创建settings.js文件"""
    settings_content = """window._CCSettings = {
    debugMode: 0,
    showFPS: true,
    frameRate: 60,
    jsList: [
        "assets/scripts/PlayerComponent.js",
        "assets/scripts/EnemyComponent.js",
        "assets/scripts/GameManager.js"
    ],
    launchScene: "assets/scenes/GameScene.fire",
    scenes: [
        {
            "url": "assets/scenes/GameScene.fire",
            "uuid": "scene_123456"
        },
        {
            "url": "assets/scenes/MenuScene.fire",
            "uuid": "scene_789012"
        }
    ],
    paths: {
        "123": ["textures/player.png"],
        "456": ["textures/enemy.png"],
        "789": ["sounds/bgm.mp3"]
    },
    types: [
        "cc.Texture2D",
        "cc.SpriteFrame",
        "cc.AudioClip",
        "cc.Prefab",
        "cc.Scene"
    ]
};
"""
    
    with open(os.path.join(test_project_path, "src", "settings.js"), "w") as f:
        f.write(settings_content)

def create_main_file():
    """创建main.js文件"""
    main_content = """// Cocos Creator Web Main File
console.log("Cocos Creator Project Starting...");

// 游戏初始化
cc.game.on(cc.game.EVENT_ENGINE_INITED, function() {
    console.log("Engine inited");
});

// 启动游戏
cc.game.run();
"""
    
    with open(os.path.join(test_project_path, "main.js"), "w") as f:
        f.write(main_content)

def create_components():
    """创建多个组件"""
    
    # PlayerComponent.js
    player_content = """cc.Class({
    name: 'PlayerComponent',
    extends: cc.Component,
    
    properties: {
        speed: {
            default: 100,
            type: cc.Float
        },
        jumpHeight: {
            default: 200,
            type: cc.Float
        },
        playerSprite: {
            default: null,
            type: cc.Sprite
        }
    },
    
    onLoad() {
        this.node.on(cc.Node.EventType.TOUCH_START, this.jump, this);
        console.log('PlayerComponent onLoad');
    },
    
    start() {
        this.moveDirection = 0;
        console.log('PlayerComponent start');
    },
    
    update(dt) {
        this.move(dt);
    },
    
    move(dt) {
        let moveX = this.speed * this.moveDirection * dt;
        this.node.x += moveX;
    },
    
    jump() {
        this.node.getComponent(cc.RigidBody).applyForceToCenter(new cc.Vec2(0, this.jumpHeight), true);
    },
    
    onDestroy() {
        this.node.off(cc.Node.EventType.TOUCH_START, this.jump, this);
    }
});
"""
    
    with open(os.path.join(test_project_path, "assets", "scripts", "PlayerComponent.js"), "w") as f:
        f.write(player_content)
    
    # EnemyComponent.js
    enemy_content = """cc.Class({
    name: 'EnemyComponent',
    extends: cc.Component,
    
    properties: {
        hp: {
            default: 100,
            type: cc.Integer
        },
        damage: {
            default: 20,
            type: cc.Integer
        },
        patrolRange: {
            default: 100,
            type: cc.Float
        }
    },
    
    onLoad() {
        this.startPos = this.node.position;
        this.direction = 1;
        console.log('EnemyComponent onLoad');
    },
    
    update(dt) {
        this.patrol(dt);
    },
    
    patrol(dt) {
        this.node.x += this.direction * 50 * dt;
        
        if (Math.abs(this.node.x - this.startPos.x) > this.patrolRange) {
            this.direction *= -1;
        }
    },
    
    takeDamage(amount) {
        this.hp -= amount;
        if (this.hp <= 0) {
            this.destroy();
        }
    }
});
"""
    
    with open(os.path.join(test_project_path, "assets", "scripts", "EnemyComponent.js"), "w") as f:
        f.write(enemy_content)
    
    # GameManager.js
    game_manager_content = """cc.Class({
    name: 'GameManager',
    extends: cc.Component,
    
    properties: {
        score: {
            default: 0,
            type: cc.Integer
        },
        playerPrefab: {
            default: null,
            type: cc.Prefab
        },
        enemyPrefab: {
            default: null,
            type: cc.Prefab
        },
        scoreLabel: {
            default: null,
            type: cc.Label
        }
    },
    
    onLoad() {
        cc.game.addPersistRootNode(this.node);
        console.log('GameManager onLoad');
    },
    
    start() {
        this.spawnPlayer();
        this.startSpawnEnemies();
        console.log('GameManager start');
    },
    
    spawnPlayer() {
        let player = cc.instantiate(this.playerPrefab);
        this.node.parent.addChild(player);
        player.position = cc.v2(0, 0);
    },
    
    startSpawnEnemies() {
        this.schedule(() => {
            this.spawnEnemy();
        }, 2);
    },
    
    spawnEnemy() {
        let enemy = cc.instantiate(this.enemyPrefab);
        this.node.parent.addChild(enemy);
        enemy.position = cc.v2(300, 0);
    },
    
    addScore(points) {
        this.score += points;
        this.scoreLabel.string = `Score: ${this.score}`;
    }
});
"""
    
    with open(os.path.join(test_project_path, "assets", "scripts", "GameManager.js"), "w") as f:
        f.write(game_manager_content)

def create_assets():
    """创建资源文件"""
    # 创建图片资源（空文件，仅用于测试）
    with open(os.path.join(test_project_path, "assets", "textures", "player.png"), "w") as f:
        f.write("// 图片资源占位符")
    
    with open(os.path.join(test_project_path, "assets", "textures", "enemy.png"), "w") as f:
        f.write("// 图片资源占位符")
    
    # 创建音频资源
    with open(os.path.join(test_project_path, "assets", "sounds", "bgm.mp3"), "w") as f:
        f.write("// 音频资源占位符")
    
    # 创建简单的bundle文件
    create_bundle_file()

def create_bundle_file():
    """创建简单的bundle文件"""
    bundle_content = """// Webpack Bundle File
(function(window, document) {
    console.log('Webpack Bundle Loaded');
    
    // 模块定义
    var modules = {
        'module1': function() {
            cc._RF.push(["","PlayerComponent","assets/scripts/PlayerComponent.js"], function() {
                cc.Class({
                    name: 'PlayerComponent',
                    extends: cc.Component,
                    
                    properties: {
                        speed: 100,
                        jumpHeight: 200
                    },
                    
                    onLoad() {
                        console.log('Bundled PlayerComponent onLoad');
                    }
                });
            });
        },
        'module2': function() {
            cc._RF.push(["","EnemyComponent","assets/scripts/EnemyComponent.js"], function() {
                cc.Class({
                    name: 'EnemyComponent',
                    extends: cc.Component,
                    
                    properties: {
                        hp: 100,
                        damage: 20
                    },
                    
                    onLoad() {
                        console.log('Bundled EnemyComponent onLoad');
                    }
                });
            });
        }
    };
    
    // 加载模块
    for (var key in modules) {
        if (modules.hasOwnProperty(key)) {
            modules[key]();
        }
    }
})(window, document);
"""
    
    with open(os.path.join(test_project_path, "assets", "gamebundle.js"), "w") as f:
        f.write(bundle_content)

# 运行测试
def run_complex_test():
    """运行复杂测试"""
    # 创建测试项目
    create_complex_project()
    
    # 运行逆向工具
    print(f"\n运行逆向工具，源路径: {test_project_path}")
    print(f"输出路径: {test_output_path}")
    
    import sys
    sys.argv = [
        "main.py",
        "--path", test_project_path,
        "--output", test_output_path,
        "--verbose"
    ]
    
    # 添加项目路径
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # 导入主函数
    from main.main import cli
    
    try:
        cli()
        print("\n复杂测试成功完成！")
        
        # 显示输出结果
        show_output_result()
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()

def show_output_result():
    """显示输出结果"""
    print(f"\n输出目录结构: {test_output_path}")
    
    for root, dirs, files in os.walk(test_output_path):
        level = root.replace(test_output_path, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")

if __name__ == "__main__":
    run_complex_test()
