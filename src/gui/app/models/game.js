import DS from 'ember-data';

export default DS.Model.extend({
    title: DS.attr('string'),
    joined: DS.attr('boolean', {defaultValue: false}),
    owned: DS.attr('boolean', {defaultValue: false}),
    sessions: DS.hasMany('Session'),
    roles: DS.hasMany('GameRole'),
});
