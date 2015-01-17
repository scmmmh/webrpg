import DS from 'ember-data';

export default DS.Model.extend({
    email: DS.attr('string'),
    display_name: DS.attr('string'),
    password: DS.attr('string'),
    
    current: function() {
        return this.id == sessionStorage.getItem('webrpg-userid'); // jshint ignore:line
    }.property('id')
});
