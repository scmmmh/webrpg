import Ember from 'ember';

export default Ember.Controller.extend({
    actions: {
        new_session: function() {
            var controller = this;
            
            var title = controller.get('session_title');
            if(title) {
                controller.store.find('user', sessionStorage.getItem('webrpg-userid')).then(function(user) {
                    var model = controller.get('model');
                    var session = controller.store.createRecord('session', {
                        title: title,
                        game: model.game
                    });
                    
                    session.save().then(function() {
                        var role = controller.store.createRecord('SessionRole', {
                            role: 'owner',
                            user: user,
                            session: session
                        });
                        role.save().then(function() {
                            controller.set('session_title', '');
                            controller.set('error', {});
                            controller.set('title', '');
                            controller.transitionToRoute('session', session.id);
                        });
                    }, function(data) {
                        controller.set('error', data.responseJSON.error.session);
                    });
                });
            } else {
                controller.set('error', {title: 'Please enter a title for your new session'});
            }
        }
    }
});
