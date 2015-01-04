import Ember from 'ember';

export default Ember.ObjectController.extend({
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
        }
    }
});
