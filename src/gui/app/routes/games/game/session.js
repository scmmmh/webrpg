import Ember from 'ember';
import AuthenticatedRouteMixin from 'ember-simple-auth/mixins/authenticated-route-mixin';

export default Ember.Route.extend(AuthenticatedRouteMixin, {
    model: function(params) {
        return this.store.findRecord('Session', params.sid);
    },
    activate: function() {
        var route = this;
        route.set('chat-messages-timer', setInterval(function() {
            route.store.query('ChatMessage', {
                session_id: 7
            });
        }, 2000));
    },
    deactivate: function() {
        clearInterval(this.get('chat-messages-timer'));
    }
});
