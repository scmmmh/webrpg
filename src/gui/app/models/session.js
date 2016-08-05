import DS from 'ember-data';

export default DS.Model.extend({
    title: DS.attr('string'),
    diceRoller: DS.attr('string'),
    
    game: DS.belongsTo('Game'),
    chatMessages: DS.hasMany('ChatMessage'),
    //maps: DS.hasMany('Map')
});
