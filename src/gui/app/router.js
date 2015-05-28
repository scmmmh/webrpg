import Ember from 'ember';
import config from './config/environment';

var Router = Ember.Router.extend({
    location: config.locationType
});

export default Router.map(function() {
    this.route('register');
    this.route('login');
    this.resource('users', { path: 'users'}, function() {
    });
    this.resource('user', { path: 'users/id/:uid' }, function() { });
    this.resource('games', function() {
        this.route('new');
    });
    this.resource('game', { path: 'games/:gid' }, function() {
        this.route('new-session');
        this.route('new-character');
    });
    this.resource('session', { path: 'sessions/:gid/:sid' }, function() { });
  this.route('game/new-character');
});
