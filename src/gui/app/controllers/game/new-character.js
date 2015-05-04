import Ember from 'ember';

export default Ember.Controller.extend({
    actions: {
        new_character: function() {
            var controller = this;
            
            var char_type = controller.get('new_character_type');
            if(char_type) {
                controller.store.find('user', sessionStorage.getItem('webrpg-userid')).then(function(user) {
                    var model = controller.get('model');
                    var character = controller.store.createRecord('character', {
                       game: model.parent.game,
                       user: user,
                       ruleSet: char_type 
                    });
                    character.save().then(function() {
                        controller.set('error', {});
                        controller.transitionToRoute('game', model.parent.game.id);
                    }, function(data) {
                        controller.set('error', data.responseJSON.error.session);
                    });
                });
            } else {
                controller.set('error', {character_type: 'Please select a character type'});
            }
        }
    }
});
