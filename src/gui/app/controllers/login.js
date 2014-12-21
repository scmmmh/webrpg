import Ember from 'ember';

export default Ember.Controller.extend({
    needs: ['application'],
    actions: {
        login: function() {
            var controller = this;
            
            var email = controller.get('email');
            var password = controller.get('password');
            
            if(email && password) {
                Ember.$.ajax('/api/users/login', {
                    'method': 'POST',
                    'dataType': 'json',
                    'data': {email: email, password: password}
                }).then(function(data) {
                    sessionStorage.setItem('webrpg-userid', data.user.id);
                    sessionStorage.setItem('webrpg-password', password);
                    controller.set('error', {});
                    controller.set('email', '');
                    controller.set('password', '');
                    controller.get('controllers.application').set('logged-in', true);
                    controller.transitionToRoute('games');
                }, function(data) {
                    controller.set('error', {
                        email: data.responseJSON['_'],
                        password: data.responseJSON['_']
                    });
                });
            } else {
                var error = {};
                if(!email) {
                    error['email'] = 'Please enter your e-mail address';
                }
                if(!password) {
                    error['password'] = 'Please enter your password';
                }
                this.set('error', error);
            }
        }
    }
});
