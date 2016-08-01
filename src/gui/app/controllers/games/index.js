import Ember from 'ember';

export default Ember.Controller.extend({
    session: Ember.inject.service('session'),
    
    actions: {
        join: function(game) {
            var controller = this;
            var user = controller.store.findRecord('user', controller.get('session').get('data.authenticated.userid'));
            user.then(function() {
                var role = controller.store.createRecord('GameRole', {
                    role: 'player',
                    game: game,
                    user: user
                });
                role.save().then(function() {
                    controller.transitionToRoute('games.game', game.get('id'));
                }, function(data) {
                    console.log(data);
                });
            });
        }
    }
});
