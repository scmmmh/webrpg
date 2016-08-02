import DS from 'ember-data';

export default DS.Model.extend({
    title: DS.attr('string'),
    diceRoller: DS.attr('string'),
    
    game: DS.belongsTo('Game'),
    //maps: DS.hasMany('Map')
});
