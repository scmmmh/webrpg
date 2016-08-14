import DS from 'ember-data';

export default DS.Model.extend({
    message: DS.attr('string'),
    formatted: DS.attr(),
    user: DS.belongsTo('User'),
    session: DS.belongsTo('Session')
});
