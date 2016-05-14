import Ember from 'ember';

export default Ember.Controller.extend({
    dice_rollers: [{'id': 'd20', 'label': 'D20'},
                   {'id': 'eote', 'label': 'Edge of the Empire'}],
    
    actions: {
        new_session: function() {
            var controller = this;
            
            var title = controller.get('session_title');
            var dice_roller = controller.get('session_dice_roller');
            if(title) {
                controller.store.find('user', sessionStorage.getItem('webrpg-userid')).then(function(user) {
                    var model = controller.get('model');
                    var session = controller.store.createRecord('session', {
                        title: title,
                        dice_roller: dice_roller.id,
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
                            controller.transitionToRoute('game', model.game.id);
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
