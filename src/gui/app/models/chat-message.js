import DS from 'ember-data';

export default DS.Model.extend({
    message: DS.attr('string'),
    user: DS.belongsTo('User'),
    session: DS.belongsTo('Session')
});
