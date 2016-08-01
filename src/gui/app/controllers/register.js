import Ember from 'ember';

export default Ember.Controller.extend({
    actions: {
        register: function() {
            var controller = this;
            var user = controller.get('store').createRecord('User', {
                'email': controller.get('email'),
                'displayName': controller.get('displayName'),
                'password': controller.get('password')
            });
            user.save().then(function() {
                controller.set('email', '');
                controller.set('displayName', '');
                controller.set('password', '');
                controller.set('errors', {});
                controller.transitionToRoute('login');
            }, function(data) {
                var errors = {};
                for(var idx=0; idx < data['errors'].length; idx++) {
                    if(data['errors'][idx].source) {
                        errors[data['errors'][idx].source] = data['errors'][idx].title;
                    }
                }
                controller.set('errors', errors);
            });
        }
    }
});
