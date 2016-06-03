import Ember from 'ember';

export default Ember.Controller.extend({
    'logged-in': function() {
        return sessionStorage.getItem('webrpg-userid') && sessionStorage.getItem('webrpg-password');
    }.property('logged-in')
});
