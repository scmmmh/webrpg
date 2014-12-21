import Ember from 'ember';

export default Ember.Route.extend({
    model: function(params) {
        return Ember.RSVP.hash({
           session: this.store.find('session', params.sid),
           chats: this.store.filter('chat-message', {session: params.sid}, function() {
               return true;
           })
        });
    }
});
