import DS from 'ember-data';

export default DS.Model.extend({
    title: DS.attr('string'),
    action: DS.attr('string'),
    columns: DS.hasMany('StatColumn'),
    parent: DS.belongsTo('StatTable'),
    
    has_action: function() {
        if(this.get('action') !== null && this.get('action') !== undefined && this.get('action') !== '') {
            return true;
        } else {
            return false;
        }
    }.property('value')
});
