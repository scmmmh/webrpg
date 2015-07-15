import DS from 'ember-data';

export default DS.Model.extend({
    value: DS.attr(),
    editable: DS.attr('boolean'),
    data_type: DS.attr('string'),
    options: DS.attr(),
    parent: DS.belongsTo('StatRow'),
    action: DS.attr('string'),
    action_title: DS.attr('string'),
    
    fancy_value: function() {
        var dt = this.get('data_type');
        var value = this.get('value');
        if(dt === 'string' || dt === 'option') {
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
        } else if (dt === 'text') {
            if(value == null || value === '') {
                return '&nbsp;';
            } else {
                return value.replace(/\n/g, '<br/>');
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
    data_option: function() {
        return this.get('data_type') === 'option';
    }.property('data_type'),
    data_text: function() {
        return this.get('data_type') === 'text';
    }.property('data_type'),
    has_action: function() {
        if(this.get('action') !== null && this.get('action') !== undefined && this.get('action') !== '') {
            return true;
        } else {
            return false;
        }
    }.property('action'),
    
    editing: DS.attr('boolean', {defaultValue: false})
});
