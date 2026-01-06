
cc.Class({
    name: 'Player',
    extends: cc.Component,
    
    properties: {
        speed: 100,
        jumpHeight: 200
    },
    
    onLoad() {
        console.log('Player onLoad');
    },
    
    start() {
        console.log('Player start');
    }
});
