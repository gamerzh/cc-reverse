// 模块名: default_module

import { _decorator, Component, Node } from 'cc';
const { ccclass, property } = _decorator;

@ccclass('TestClass')
export class TestClass extends cc.Component {
  @property
  speed: any = 100;

  @property
  jumpHeight: any = 200;

  // 生命周期函数 - 只在第一个组件实例上调用一次
  protected onLoad(): void {
        console.log('TestClass onLoad');
  }

  // 生命周期函数 - 每次组件实例激活时调用
  protected start(): void {
    // 组件开始运行时的代码
  }

  // 每一帧更新时调用
  protected update(deltaTime: number): void {
    // 每一帧更新的代码

  static get __input(): number {
        return this._input || 0;
  }

  static set __input(v: number) {
        this._input = value;
  }

}
