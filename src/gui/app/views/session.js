import Ember from 'ember';

export default Ember.View.extend({
    chat_message_observer: function() {
        Ember.run.scheduleOnce('afterRender', this, this.chat_message_scroll_update);
    }.observes('controller.model.chats.[]'),
    chat_message_scroll_update: function() {
        var messages = this.$('.messages');
        var scrollTop = messages.scrollTop();
        var innerHeight = messages.innerHeight();
        var last_top = messages.children(':last-child()').position().top;
        if(scrollTop + innerHeight / 2 > last_top) {
            this.$('.messages').scrollTop(scrollTop + 1000);
        }
    },
    update_layout: function() {
        var height = Ember.$(window).innerHeight();
        this.$().siblings().each(function() {
           height = height - Ember.$(this).outerHeight(true); 
        });
        this.$('#session-content').siblings().each(function() {
           height = height - Ember.$(this).outerHeight(true); 
        });
        this.$('#session-content').css('height', height + 'px');
    },
    setup_view: function() {
        var view = this;
        view.update_layout();
        Ember.$(window).on('resize.session', function() {
            view.update_layout();
        });
        var mx = 0;
        var my = 0;
        var offset = null;
        var mouse_down = false;
        var map = this.$('#maps');
        var controller = this.get('controller');
        this.$('#fog-edit').on('mousemove.session', function(position) {
            if(!offset) {
                offset = Ember.$(this).offset();
            }
            mx = position.clientX;
            my = position.clientY;
            if(mouse_down) {
                var x = mx - offset.left;
                var y = my - offset.top + map.scrollTop();
                var radius = controller.get('map_cursor_size');
                var ctx = this.getContext('2d');
                ctx.save();
                ctx.beginPath();
                ctx.arc(x, y, radius, 0, 2*Math.PI, true);
                ctx.clip();
                ctx.clearRect(x-radius,y-radius,radius*2,radius*2);
                ctx.restore();
            }
        });
        this.$('#fog-edit').on('mousedown.session', function() {
            mouse_down = true;
        });
        this.$('#fog-edit').on('mouseup.session', function() {
            mouse_down = false;
            view.get('controller').send('update-fog');
        });
    }.on('didInsertElement'),
    destroy_view: function() {
        Ember.$(window).off('resize.session');
        this.$('#fog-edit').off('mousemove.session');
        this.$('#fog-edit').off('mouseup.session');
        this.$('#fog-edit').off('mousedown.session');
    }
});
