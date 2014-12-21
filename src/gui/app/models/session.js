import DS from 'ember-data';

export default DS.Model.extend({
    title: DS.attr('string'),
    game: DS.belongsTo('Game', {async: true}),
    roles: DS.hasMany('SessionRole', {async: true}),
    
    joined: DS.attr('boolean', {default_value: true})
});
