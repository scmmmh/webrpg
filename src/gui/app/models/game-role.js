import Ember from 'ember';
import DS from 'ember-data';

export default DS.Model.extend({
    role: DS.attr('string'),
    is_me: DS.attr('boolean', {defaultValue: false}),
    user: DS.belongsTo('User'),
    game: DS.belongsTo('Game'),
});
