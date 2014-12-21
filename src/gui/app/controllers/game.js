import Ember from 'ember';

export default Ember.ObjectController.extend({
    actions: {
        join_session: function(sid) {
            var controller = this;
            
            Ember.RSVP.hash({
                user: controller.store.find('User', sessionStorage.getItem('webrpg-userid')),
                session: controller.store.find('Session', sid)
            }).then(function(data) {
                var role = controller.store.createRecord('SessionRole', {
                    role: 'player',
                    user: data.user,
                    session: data.session
                });
                role.save().then(function() {
                    controller.transitionToRoute('session', sid);
                });
            });
        }
    }
});
