import Ember from 'ember';
import config from './config/environment';

var Router = Ember.Router.extend({
    location: config.locationType
});

Router.map(function() {
    this.route('register');
    this.route('login');
    this.resource('users', { path: 'users'}, function() {
    });
    this.resource('user', { path: 'users/id/:uid' }, function() { });
    this.resource('games', function() {
        this.route('new');
    });
    this.resource('game', { path: 'games/:gid' }, function() {
        this.route('new_session');
    });
    this.resource('session', { path: 'sessions/:sid' }, function() { });
});

export default Router;
