import Ember from 'ember';

export default Ember.ArrayController.extend({
    needs: ['application'],
    actions: {
        join_game: function(gid) {
            var controller = this;
            
            Ember.RSVP.hash({
                game: controller.store.find('Game', gid),
                user: controller.store.find('User', sessionStorage.getItem('webrpg-userid'))
            }).then(function(data) {
                var role = controller.store.createRecord('GameRole', {
                    role: 'player',
                    game: data.game,
                    user: data.user
                });
                role.save().then(function() {
                    controller.transitionToRoute('game', data.game.get('id'));
                });
            });
        }
    }
});
