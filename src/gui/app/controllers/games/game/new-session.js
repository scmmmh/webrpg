import Ember from 'ember';

export default Ember.Controller.extend({
    parent: Ember.inject.controller('games.game'),
    
    actions: {
        create: function() {
            var controller = this;
            var game = controller.get('parent.model');
            var session = controller.store.createRecord('Session', {
                title: controller.get('title'),
                diceRoller: controller.get('dice-roller'),
                game: game
            });
            session.save().then(function() {
                controller.set('title', '');
                controller.set('dice-roller', '');
                controller.transitionToRoute('games.game.session', game.id, session.id);
            }, function(data) {
                var errors = {};
                for(var idx=0; idx < data['errors'].length; idx++) {
                    if(data['errors'][idx].source) {
                        errors[data['errors'][idx].source] = data['errors'][idx].title;
                    } else {
                        errors['title'] = data['errors'][idx].title;
                    }
                }
                controller.set('errors', errors);
            });
        }
    }
});
