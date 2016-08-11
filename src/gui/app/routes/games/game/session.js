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
        var controller = route.controllerFor('games.game.session');
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
                    message.set('newMessage', true);
                    setTimeout(function() {
                        message.set('newMessage', false);
                    }, 5000);
                });
                route.set('chat-message-min-id', max_id);
                if(controller.get('chatMessageAutoScroll')) {
                    Ember.run.schedule('afterRender', this, function() {
                        var messages = Ember.$('.chat-message-list');
                        if(messages.children(':last-child()').length > 0) {
                            var last_top = messages.children(':last-child()').position().top;
                            Ember.$('.chat-message-list').scrollTop(messages.scrollTop() + last_top);
                        }
                    });
                }
            }
        });
        route.set('chat-messages-timer', setTimeout(function() {
            route.updateChat();
        }, 1000));
    }
});
