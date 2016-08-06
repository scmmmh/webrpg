import Ember from 'ember';
import config from './config/environment';

const Router = Ember.Router.extend({
  location: config.locationType,
  rootURL: config.rootURL
});

Router.map(function() {
  this.route('login');
  this.route('games', function() {
    this.route('new');
    this.route('game', {path: '/:gid'}, function() {
      this.route('new-session');
      this.route('session', {path: '/:sid'});
      this.route('new-character');
    });
  });
  this.route('register');
});

export default Router;
