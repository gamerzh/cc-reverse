// 测试模块
cc._RF.push(t, "test123", "TestModule");

cc.Class({
  name: "TestUI",
  extends: cc.Component,
  properties: {
    label: { default: null, type: cc.Label },
    score: { default: 0, type: Number }
  },
  onLoad: function() {
    console.log("TestUI loaded");
  },
  start: function() {
    this.updateScore();
  },
  updateScore: function() {
    if (this.label) {
      this.label.string = "Score: " + this.score;
    }
  }
});

// 静态字段
e._config = { host: "localhost", port: 8080 };
Object.defineProperty(e, "version", {
  get: function() { return "1.0.0"; }
});

cc._RF.pop();