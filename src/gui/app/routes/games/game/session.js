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
    },
    deactivate: function() {
        clearInterval(this.get('chat-messages-timer'));
    }
});
