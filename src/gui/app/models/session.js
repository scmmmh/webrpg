import DS from 'ember-data';

export default DS.Model.extend({
    title: DS.attr('string'),
    dice_roller: DS.attr('string'),
    game: DS.belongsTo('Game', {async: true}),
    roles: DS.hasMany('SessionRole', {async: true}),
    maps: DS.hasMany('Map', {async: true}),
    
    joined: DS.attr('boolean', {default_value: true})
});
