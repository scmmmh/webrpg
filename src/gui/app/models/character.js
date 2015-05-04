import DS from 'ember-data';

export default DS.Model.extend({
    attr: DS.attr(),
    game: DS.belongsTo('Game', {async: true}),
    user: DS.belongsTo('User', {async: true}),
    ruleSet: DS.belongsTo('RuleSet', {async: true}),
    stats: DS.hasMany('StatTable')
});
