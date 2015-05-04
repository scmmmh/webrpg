import DS from 'ember-data';

export default DS.Model.extend({
    title: DS.attr('string'),
    columns: DS.attr(),
    rows: DS.hasMany('StatRow'),
    parent: DS.belongsTo('Character'),
});
