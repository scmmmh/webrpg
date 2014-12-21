import Ember from 'ember';

export default Ember.Controller.extend({
    actions: {
        register: function() {
            var controller = this;
            
            var new_email = controller.get('email');
            var new_display_name = controller.get('display_name');
            var new_password = controller.get('password');
            var new_confirm_password = controller.get('confirm_password');
            
            if(new_email && new_display_name && new_password && new_confirm_password && new_password === new_confirm_password) {
                var new_user = controller.store.createRecord('user', {
                    email: new_email,
                    display_name: new_display_name,
                    password: new_password
                });
                new_user.save().then(function(user) {
                    sessionStorage.setItem('webrpg-userid', user.id);
                    sessionStorage.setItem('webrpg-password', new_password);
                    controller.set('error', {});
                    controller.set('email', '');
                    controller.set('display_name', '');
                    controller.set('password', '');
                    controller.set('confirm_password', '');
                    controller.get('controllers.application').set('logged-in', true);
                    controller.transitionToRoute('games');
                }, function(data) {
                    controller.set('error', data.responseJSON.error.user);
                });
            } else {
                var error = {};
                if(!new_email) {
                    error['email'] = 'Please provide an e-mail address';
                }
                if(!new_display_name) {
                    error['display_name'] = 'Please provide a nickname';
                }
                if(!new_password) {
                    error['password'] = 'Please provide a password';
                }
                if(!new_confirm_password) {
                    error['confirm_password'] = 'Please confirm your password';
                }
                if(new_password && new_confirm_password && new_password !== new_confirm_password) {
                    error['password'] = 'Your password does not match the confirmation';
                    error['confirm_password'] = 'Your password does not match the confirmation';
                }
                this.set('error', error);
            }
        }
    }
});
