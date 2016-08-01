import Ember from 'ember';
import DS from 'ember-data';

export default DS.Model.extend({
    role: DS.attr('string'),
    is_me: DS.attr('boolean', {defaultValue: false}),
    user: DS.belongsTo('User'),
    game: DS.belongsTo('Game'),
    
    is_not_me: Ember.computed('is_me', function() {
        return !this.get('is_me');
    }),
    is_owner: Ember.computed('role', function() {
        return this.get('role') === 'owner';
    }),
    is_player: Ember.computed('role', function() {
        return this.get('role') === 'player';
    })
});
