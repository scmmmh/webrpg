import Ember from 'ember';

export default Ember.Component.extend({
    actions: {
        'start-edit': function(character, column) {
            Ember.set(column, 'isEditing', true);
            Ember.set(column, 'oldValue', Ember.get(column, 'value'));
        },
        'cancel-edit': function(character, column) {
            Ember.set(column, 'isEditing', false);
            Ember.set(column, 'value', Ember.get(column, 'oldValue'));
        },
        'save-edit': function(character, column) {
            Ember.set(column, 'isEditing', false);
            character.save();
        },
    }
});
