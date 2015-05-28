import Ember from 'ember';


var AutoUpdater = Ember.Object.extend({
    schedule: function() {
        return Ember.run.later(this, function() {
            this.update();
            this.set('timer', this.schedule());
        }, 1000);
    },
    start: function() {
        this.set('timer', this.schedule());
    },
    stop: function() {
        Ember.run.cancel(this.get('timer'));
    },
    update: function() {
        var updater = this;
        var min_ids = {};
        if(!Ember.isNone(this.get('min_chat_message_id'))) {
            min_ids['chatMessages'] = this.get('min_chat_message_id');
        }
        if(!Ember.isNone(this.get('session_id'))) {
            var userid = sessionStorage.getItem('webrpg-userid');
            var password = sessionStorage.getItem('webrpg-password');
            Ember.$.ajax('/api/sessions/' + this.get('session_id') + '/refresh', {
                dataType: 'json',
                data: min_ids,
                headers: {
                    'X-WebRPG-Authentication': userid + ':' + password
                }
            }).done(function(data) {
                var min_chat_message_id = updater.get('min_chat_message_id');
                data.chatMessages.forEach(function(chat_message) {
                    if(!updater.get('route.store').recordIsLoaded('chat-message', chat_message.id)) {
                        updater.get('route.store').push('chat-message', chat_message);
                    }
                    if(!min_chat_message_id || chat_message.id > min_chat_message_id) {
                        min_chat_message_id = chat_message.id;
                    } 
                });
                updater.set('min_chat_message_id', min_chat_message_id);
            });
        }
    }
});


export default Ember.Route.extend({
    model: function(params) {
        var promise = Ember.RSVP.hash({
           session: this.store.find('session', params.sid),
           chats: this.store.filter('chat-message', {session: params.sid}, function() {
               return true;
           }),
           characters: this.store.find('character', {
               game_id: params.gid,
               user_id: sessionStorage.getItem('webrpg-userid')
           })
        });
        return promise;
    },
    setupController: function(controller, model) {
    	controller.set('model', model);
    	if(Ember.isNone(this.get('updater'))) {
    	    this.set('updater', AutoUpdater.create({
    	        'route': this
    	    }));
    	}
    	this.get('updater').start();
    	var min_chat_message_id;
    	model.chats.forEach(function (message) {
    	    if(!min_chat_message_id || message.id > min_chat_message_id) {
    	        min_chat_message_id = message.id;
    	    }
    	});
    	this.get('updater').set('min_chat_message_id', min_chat_message_id);
    	this.get('updater').set('session_id', model.session.id);
    },
    deactivate: function() {
    	this.get('updater').stop();
    }
});
