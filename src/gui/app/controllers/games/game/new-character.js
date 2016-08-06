import Ember from 'ember';

export default Ember.Controller.extend({
    session: Ember.inject.service('session'),
    parent: Ember.inject.controller('games.game'),
    
    actions: {
        create: function() {
            var controller = this;
            var game = controller.get('parent.model');
            var user = controller.store.findRecord('user', controller.get('session.data.authenticated.userid'));
            user.then(function() {
                var session = controller.store.createRecord('Character', {
                    game: game,
                    user: user,
                    ruleSet: controller.get('rule-set')
                });
                session.save().then(function() {
                    controller.set('rule-set', '');
                    controller.transitionToRoute('games.game', game.id);
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
            });
        }
    }
});
