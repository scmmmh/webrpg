import Ember from 'ember';


var AutoUpdater = Ember.Object.extend({
    schedule: function() {
        return Ember.run.later(this, function() {
            this.update();
            this.set('timer', this.schedule());
        }, this.get('interval'));
    },
    start: function() {
        this.set('timer', this.schedule());
    },
    stop: function() {
        Ember.run.cancel(this.get('timer'));
    },
    update: function() {
        this.get('action').call(this);
    }
});


export default Ember.Route.extend({
    model: function(params) {
        var promise = Ember.RSVP.hash({
            game: this.store.findRecord('game', params.gid),
            session: this.store.findRecord('session', params.sid),
            chats: this.store.filter('chat-message', {session: params.sid}, function() {
                return true;
            }),
            characters: this.store.query('character', {
                game_id: params.gid,
                user_id: sessionStorage.getItem('webrpg-userid')
            })
        });
        promise.then(function(data) {
            data.game.get('roles').then(function(roles) {
                roles.forEach(function(role) {
                    if(role.get('role') === 'owner') {
                        role.get('user').then(function(user) {
                            if(user.get('id') == sessionStorage.getItem('webrpg-userid')) { // jshint ignore:line
                                data.game.set('owned', true); 
                            } 
                        });
                    }
                });
            });
        });
        return promise;
    },
    setupController: function(controller, model) {
    	controller.set('model', model);
        if(Ember.isNone(this.get('chat-updater'))) {
            this.set('chat-updater', AutoUpdater.create({
                'route': this,
                'interval': 1000,
                'action': function() {
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
            }));
        }
        if(Ember.isNone(this.get('session-updater'))) {
            this.set('session-updater', AutoUpdater.create({
                'route': this,
                'interval': 10000,
                'action': function() {
                    if(!Ember.isNone(this.get('session_id'))) {
                        this.route.get('controller').get('model').session.reload();
                        var current_map = this.route.get('controller').get('current_map');
                        if(!Ember.isNone(current_map)) {
                            current_map.reload();
                        }
                    }
                }
            }));
        }
    	this.get('chat-updater').start();
    	this.get('session-updater').start();
    	var min_chat_message_id;
    	model.chats.forEach(function (message) {
    	    if(!min_chat_message_id || message.id > min_chat_message_id) {
    	        min_chat_message_id = message.id;
    	    }
    	});
    	this.get('chat-updater').set('min_chat_message_id', min_chat_message_id);
        this.get('chat-updater').set('session_id', model.session.id);
        this.get('session-updater').set('session_id', model.session.id);
    },
    deactivate: function() {
        this.get('chat-updater').stop();
        this.get('session-updater').stop();
    }
});
