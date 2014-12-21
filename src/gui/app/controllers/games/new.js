import Ember from 'ember';

export default Ember.Controller.extend({
    actions: {
        new_game: function() {
            var controller = this;
            
            var title = controller.get('title');
            if(title) {
                controller.store.find('user', sessionStorage.getItem('webrpg-userid')).then(function(user) {
                    var game = controller.store.createRecord('game', {
                        title: title
                    });
                    
                    game.save().then(function() {
                        var role = controller.store.createRecord('GameRole', {
                            role: 'owner',
                            user: user,
                            game: game
                        });
                        role.save().then(function() {
                            controller.set('error', {});
                            controller.set('title', '');
                            controller.transitionToRoute('game', game.id);
                        });
                    }, function(data) {
                        controller.set('error', data.responseJSON.error.game);
                    });
                    
                });
            } else {
                controller.set('error', {title: 'Please provide a title for the new game'});
            }
        }
    }
});
