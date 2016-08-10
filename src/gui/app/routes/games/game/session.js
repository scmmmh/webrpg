import Ember from 'ember';
import AuthenticatedRouteMixin from 'ember-simple-auth/mixins/authenticated-route-mixin';

export default Ember.Route.extend(AuthenticatedRouteMixin, {
    model: function(params) {
        this.set('params', params);
        return this.store.findRecord('Session', params.sid);
    },
    activate: function() {
        var route = this;
        var controller = route.controllerFor('games.game.session');
        controller.set('selectedMap', null);
        route.set('chat-messages-timer', setTimeout(function() {
            route.updateChat();
        }, 1000));
        Ember.run.schedule("afterRender",this,function() {
            var height = (Ember.$(window).innerHeight() - (Ember.$('.top-bar').outerHeight(true) + Ember.$('h1').outerHeight(true)));
            if(navigator.userAgent.indexOf('Edge/') >= 0) { // Hack for MS Edge
                height = height - 20;
            }
            Ember.$('#session-window').css('height', height + 'px');
            Ember.$('.chat-message-list').scrollTop(100000);
        });
        Ember.$(window).on('resize', function() {
            clearTimeout(route.get('window-resize-timeout'));
            route.set('window-resize-timeout', setTimeout(function() {
                Ember.run.schedule("afterRender",this, function() {
                    Ember.$('#session-window').css('height', (Ember.$(window).innerHeight() - (Ember.$('.top-bar').outerHeight(true) + Ember.$('h1').outerHeight(true))) + 'px');
                });
            }, 100));
        });
    },
    deactivate: function() {
        clearTimeout(this.get('chat-messages-timer'));
        Ember.$(window).off('resize');
    },
    updateChat: function() {
        var route = this;
        var query = {
            session_id: route.get('params').sid
        };
        if(route.get('chat-message-min-id')) {
            query['$gt:id'] = route.get('chat-message-min-id');
        }
        route.store.query('ChatMessage', query).then(function(data) {
            if(data.get('length') > 0) {
                var max_id = 0;
                data.forEach(function(message) {
                    max_id = Math.max(max_id, message.get('id'));
                });
                route.set('chat-message-min-id', max_id);
            }
            Ember.run.schedule('afterRender', this, function() {
                var messages = Ember.$('.chat-message-list');
                var scrollTop = messages.scrollTop();
                var innerHeight = messages.innerHeight();
                var last_top = messages.children(':last-child()').position().top;
                if(scrollTop + innerHeight / 2 > last_top) {
                    Ember.$('.chat-message-list').scrollTop(scrollTop + 1000);
                }
            });
        });
        route.set('chat-messages-timer', setTimeout(function() {
            route.updateChat();
        }, 1000));
    }
});
