import Ember from 'ember';

AutoUpdater = Ember.Object.extend({
	schedule: function() {
		
	},
	start: function() {
		this.set('timer', this.schedule(this.get('update')));
	},
	stop: function() {
		
	},
	update: function() {
		
	}
});

export default Ember.Route.extend({
    model: function(params) {
        return Ember.RSVP.hash({
           session: this.store.find('session', params.sid),
           chats: this.store.filter('chat-message', {session: params.sid}, function() {
               return true;
           })
        });
    },
    setupController: function() {
    	
    },
    deactivate: function() {
    	
    }
});
