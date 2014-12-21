import DS from 'ember-data';

export default DS.Model.extend({
    role: DS.attr('string'),
    user: DS.belongsTo('User', {async: true}),
    session: DS.belongsTo('Session', {async: true})
});
