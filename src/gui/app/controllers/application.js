import Ember from 'ember';

export default Ember.Controller.extend({
    'logged-in': function() {
        return sessionStorage.getItem('webrpg-userid') && sessionStorage.getItem('webrpg-password');
    }.property('logged-in'),
    actions: {
        logout: function() {
            sessionStorage.clear('webrpg-userid');
            sessionStorage.clear('webrpg-password');
            this.set('logged-in', false);
            this.transitionToRoute('index');
        }
    }
});
