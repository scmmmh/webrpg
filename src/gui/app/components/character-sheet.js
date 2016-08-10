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
            var controller = this;
            Ember.set(column, 'isEditing', false);
            character.save();
        },
        'delete': function(character) {
            if(confirm('Please confirm you wish to delete this character')) {
                character.deleteRecord();
                character.save();
            }
        },
        'reload': function(character) {
            var controller = this;
            character.reload();
        },
        'selectTab': function(tab) {
            this.set('selectedTab', tab);
        }
    }
});
