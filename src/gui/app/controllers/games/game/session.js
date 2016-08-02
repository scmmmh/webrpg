import Ember from 'ember';

export default Ember.Controller.extend({
    parent: Ember.inject.controller('games.game')
});
