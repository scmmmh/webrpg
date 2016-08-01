import Ember from 'ember';

export default Ember.Controller.extend({
    session: Ember.inject.service('session'),
    
    actions: {
        login: function() {
            var controller = this;
            controller.get('session').authenticate('authenticator:webrpg', controller.get('email'), controller.get('password')).then(function() {
                controller.set('email', '');
                controller.set('password', '');
                controller.set('error', {});
                controller.transitionToRoute('games');
            }, function(data) {
                var errors = {};
                for(var idx=0; idx < data['errors'].length; idx++) {
                    if(data['errors'][idx].source) {
                        errors[data['errors'][idx].source] = data['errors'][idx].title;
                    } else {
                        errors['email'] = data['errors'][idx].title;
                    }
                }
                controller.set('errors', errors);
            });
        }
    }
});
