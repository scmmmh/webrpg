import DS from 'ember-data';

export default DS.Model.extend({
    title: DS.attr('string'),
    ruleSet: DS.attr('string'),
    stats: DS.attr(),
    game: DS.belongsTo('Game'),
    user: DS.belongsTo('User')
});
