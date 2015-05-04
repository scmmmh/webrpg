import DS from 'ember-data';

export default DS.Model.extend({
    value: DS.attr(),
    editable: DS.attr('boolean'),
    data_type: DS.attr('string'),
    parent: DS.belongsTo('StatRow'),
    
    fancy_value: function() {
        var dt = this.get('data_type');
        var value = this.get('value');
        if(dt === 'string') {
            if(value == null || value === '') {
                return '&nbsp;';
            } else {
                return value;
            }
        } else if (dt === 'number') {
            if(value == null || value === '') {
                return '&nbsp;';
            } else if(value > 0) {
                return '+' + value;
            } else {
                return value;
            }
        } else if (dt === 'boolean') {
            if(value) {
                return '<span class="fi-check"></span>';
            } else {
                return '&nbsp;';
            }
        }
    }.property('value'),
    data_string: function() {
        return this.get('data_type') === 'string';
    }.property('data_type'),
    data_number: function() {
        return this.get('data_type') === 'number';
    }.property('data_type'),
    data_boolean: function() {
        return this.get('data_type') === 'boolean';
    }.property('data_type'),
    
    editing: DS.attr('boolean', {defaultValue: false})
});
