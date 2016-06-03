import Ember from 'ember';

export default Ember.Controller.extend({
    application: Ember.inject.controller(),
    actions: {
        login: function() {
            var controller = this;
            
            Ember.$.ajax('/api/users/login', {
                'method': 'POST',
                'dataType': 'json',
                'data': {
                    email: controller.get('email'),
                    password: controller.get('password')
                }
            }).then(function(data) {
                sessionStorage.setItem('webrpg-userid', data.user.id);
                sessionStorage.setItem('webrpg-password', controller.get('password'));
                controller.set('error', {});
                controller.set('email', '');
                controller.set('password', '');
                controller.get('application').set('logged-in', true);
                controller.transitionToRoute('games');
            }, function(jqXHR) {
                controller.set('error', jqXHR.responseJSON);
                controller.get('application').set('logged-in', false);
            });
        }
    }
});
