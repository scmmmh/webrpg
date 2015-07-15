import Ember from 'ember';

export default Ember.Controller.extend({
    actions: {
        new_chat_message: function() {
            var controller = this;
            
            var message = controller.get('new_chat_message');
            if(message) {
                var session = controller.get('model').session;
                controller.store.find('User', sessionStorage.getItem('webrpg-userid')).then(function(user) {
                    var chat_message = controller.store.createRecord('ChatMessage', {
                        message: message,
                        user: user,
                        session: session
                    }); 
                    chat_message.save().then(function() {
                        controller.set('new_chat_message', ''); 
                    });
                });
            }
        },
        'stat-click': function(character, stat) {
            if(stat.get('has_action')) {
                if(this.get('model').characters.get('length') > 1) {
                    this.set('new_chat_message', character.get('title') + ' ' + stat.get('action_title') + ': ' + stat.get('action'));
                } else {
                    this.set('new_chat_message', stat.get('action_title') + ': ' + stat.get('action'));
                }
                $('#chat-message-input').focus();
            }
        },
        'new-snapshot': function() {
            window.Webcam.set({
                width: 320,
                height: 240
            });
            window.Webcam.attach('#video');
            Ember.$('#snapshot-ui').show();
        },
        'cancel-snapshot': function() {
            window.Webcam.reset();
            Ember.$('#snapshot-ui').hide();
        },
        snapshot: function() {
            window.Webcam.snap(function(uri) {
                Ember.$('#target').attr('src', uri);
            });
        }
    }
});
