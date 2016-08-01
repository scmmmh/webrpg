import Ember from 'ember';

export default Ember.Controller.extend({
    session: Ember.inject.service('session'),
    
    actions: {
        create: function() {
            var controller = this;
            var game = controller.store.createRecord('Game', {
                title: controller.get('title')
            });
            var user = controller.store.findRecord('user', controller.get('session').get('data.authenticated.userid'));
            game.save().then(function() {
                user.then(function() {
                    var role = controller.store.createRecord('GameRole', {
                        role: 'owner',
                        game: game,
                        user: user
                    });
                    role.save().then(function() {
                        controller.set('title', '');
                        controller.transitionToRoute('games.game', game.get('id'));
                    }, function(data) {
                        console.log(data);
                    });
                });
            }, function(data) {
                var errors = {};
                for(var idx=0; idx < data['errors'].length; idx++) {
                    if(data['errors'][idx].source) {
                        errors[data['errors'][idx].source] = data['errors'][idx].title;
                    } else {
                        errors['title'] = data['errors'][idx].title;
                    }
                }
                console.log(errors);
                controller.set('errors', errors);
            });
        }
    }
});
