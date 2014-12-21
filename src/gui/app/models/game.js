import DS from 'ember-data';

export default DS.Model.extend({
    title: DS.attr('string'),
    sessions: DS.hasMany('Session', {async: true}),
    roles: DS.hasMany('GameRole', {async: true}),
    
    joined: DS.attr('boolean', {defaultValue: false}),
    owned: DS.attr('boolean', {defaultValue: false})
});
