import Ember from 'ember';

export default Ember.Controller.extend({
    session: Ember.inject.service('session'),
    
    init: function () {
        this._super();
        Ember.run.schedule("afterRender",this,function() {
            Ember.$('#session-window').css('height', (Ember.$(window).innerHeight() - (Ember.$('.top-bar').outerHeight(true) + Ember.$('h1').outerHeight(true))) + 'px');
        });
    },
    
    actions: {
        addChatMessage: function() {
            var controller = this;
            var user = controller.store.findRecord('user', controller.get('session.data.authenticated.userid'));
            user.then(function() {
                var txt = controller.get('chatMessage');
                if(txt !== '') {
                    var message = controller.store.createRecord('chatMessage', {
                        message: txt,
                        user: user,
                        session: controller.get('model')
                    });
                    message.save().then(function() {
                        controller.set('chatMessage', '');
                    });
                }
            });
        },
        csAction: function(type, title, content) {
            if(type == 'chat') {
                this.set('chatMessage', title + ': ' + content);
                Ember.$('.chat input[type=text').focus();
            }
        }
    }
});
