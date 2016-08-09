import Ember from 'ember';

export default Ember.Component.extend({
    tagName: 'canvas',
    classNames: ['map-fog'],
    
    map: undefined,
    'map-img': new Image(),
    'map-fog': new Image(),
    
    didInsertElement: function() {
        var component = this;
        component.initCanvas();
        var canvas = component.$();
        var offset = canvas.offset();
        offset.top = offset.top + canvas.parent().scrollTop();
        offset.left = offset.left + canvas.parent().scrollLeft();
        component.set('offset', offset);
    },
    mapChanged: Ember.observer('map.map', function() {
        this.initCanvas();
    }),
    initCanvas: function() {
        var component = this;
        var mapImg = new Image();
        mapImg.onload = function() {
            var canvas = component.$();
            canvas.attr('width', this.width).attr('height', this.height);
            var ctx = canvas[0].getContext('2d');
            if(component.get('map.fog')) {
                var fogImg = new Image();
                fogImg.onload = function() {
                    ctx.drawImage(this, 0, 0);
                    fogImg.onload = null;
                };
                fogImg.src = component.get('map.fog');
                component.set('map-fog', fogImg);
            } else {
                ctx.fillStyle = '#ffffff';
                ctx.fillRect(0, 0, this.width, this.height);
                component.set('map.fog', canvas[0].toDataURL());
                component.set('map-fog.src', canvas[0].toDataURL());
                component.get('map').save().then(function() {
                    component.set('map.saving', false);
                }, function() {
                    component.set('map.saving', false);
                });
            }
        };
        mapImg.src = component.get('map.map');
        component.set('map-img', mapImg);
    },
    mouseMove: function(ev) {
        this.updateCanvas(ev);
    },
    mouseDown: function(ev) {
        var component = this;
        var canvas = component.$();
        var ctx = canvas[0].getContext('2d');
        ctx.clearRect(0, 0, canvas.attr('width'), canvas.attr('height'));
        ctx.drawImage(component.get('map-fog'), 0, 0);
        component.set('isFirstDraw', true);
        component.set('isMouseDown', true);
        component.updateCanvas(ev);
    },
    mouseUp: function(ev) {
        var component = this;
        component.set('isMouseDown', false);
        component.set('map.fog', component.$()[0].toDataURL());
        component.set('map-fog.src', component.$()[0].toDataURL());
        component.set('map.saving', true);
        component.get('map').save().then(function() {
            component.set('map.saving', false);
        }, function() {
            component.set('map.saving', false);
        });
    },
    updateCanvas: function(ev) {
        var component = this;
        var canvas = component.$();
        var mx = Math.floor(ev.clientX - component.get('offset.left') + canvas.parent().scrollLeft());
        var my = Math.floor(ev.clientY - component.get('offset.top') + canvas.parent().scrollTop());
        var radius = component.get('cursorSize');
        var ctx = canvas[0].getContext('2d');
        if(component.get('isMouseDown')) {
            if(component.get('cursorMode') === 'reveal') {
                ctx.save();
                ctx.beginPath();
                ctx.arc(mx, my, radius + 1, 0, 2 * Math.PI, true);
                ctx.clip();
                ctx.clearRect(mx - radius - 1, my - radius - 1, (radius + 1) * 2, (radius + 1) * 2);
                ctx.restore();
            } else if(component.get('cursorMode') === 'hide') {
                ctx.fillStyle = '#ffffff';
                ctx.beginPath();
                ctx.arc(mx, my, radius + 1, 0, 2 * Math.PI, true);
                ctx.fill();
            }
        } else {
            ctx.clearRect(0, 0, canvas.attr('width'), canvas.attr('height'));
            ctx.drawImage(component.get('map-fog'), 0, 0);
            ctx.beginPath();
            ctx.arc(mx, my, radius, 0, 2 * Math.PI, true);
            ctx.stroke();
        }
    },
    mouseLeave: function(ev) {
        var component = this;
        var canvas = component.$();
        var ctx = canvas[0].getContext('2d');
        ctx.drawImage(component.get('map-fog'), 0, 0);
    }
});
