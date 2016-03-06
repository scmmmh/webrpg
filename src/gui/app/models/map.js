import DS from 'ember-data';

export default DS.Model.extend({
    title: DS.attr('string'),
    map: DS.attr('string'),
    fog: DS.attr('string'),
    session: DS.belongsTo('session', {async: true})
});
