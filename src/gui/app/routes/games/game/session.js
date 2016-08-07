import Ember from 'ember';
import AuthenticatedRouteMixin from 'ember-simple-auth/mixins/authenticated-route-mixin';

export default Ember.Route.extend(AuthenticatedRouteMixin, {
    model: function(params) {
        this.set('params', params);
        return this.store.findRecord('Session', params.sid);
    },
    activate: function() {
        var route = this;
        var params = route.get('params');
        route.set('chat-messages-timer', setInterval(function() {
            route.store.query('ChatMessage', {
                session_id: params.sid
            });
        }, 2000));
        Ember.run.schedule("afterRender",this,function() {
            Ember.$('#session-window').css('height', (Ember.$(window).innerHeight() - (Ember.$('.top-bar').outerHeight(true) + Ember.$('h1').outerHeight(true))) + 'px');
        });
        Ember.$(window).on('resize', function() {
            clearTimeout(route.get('window-resize-timeout'));
            route.set('window-resize-timeout', setTimeout(function() {
                Ember.run.schedule("afterRender",this,function() {
                    Ember.$('#session-window').css('height', (Ember.$(window).innerHeight() - (Ember.$('.top-bar').outerHeight(true) + Ember.$('h1').outerHeight(true))) + 'px');
                });
            }, 100));
        });
    },
    deactivate: function() {
        clearInterval(this.get('chat-messages-timer'));
        Ember.$(window).off('resize');
    }
});
