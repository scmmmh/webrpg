import Ember from 'ember';

export default Ember.Component.extend({
    didInsertElement: function() {
    	var controller = this;
        Ember.$('.accordion').foundation();
        Ember.$('.accordion').on('down.zf.accordion', function(_, tab) {
            controller.set('selected-tab', tab.data('itemId'));
        });
        Ember.$('.accordion').on('up.zf.accordion', function() {
            controller.set('selected-tab', '');
        });
    },
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
            character.save().then(function() {
            	Ember.run.schedule('afterRender', function() {
            		Foundation.reInit(controller.$('.accordion'));
            	});
            });
        },
        'delete': function(character) {
            if(confirm('Please confirm you wish to delete this character')) {
                character.deleteRecord();
                character.save();
            }
        },
        'reload': function(character) {
            var controller = this;
            character.reload().then(function() {
                Ember.run.schedule('afterRender', function() {
                    Foundation.reInit(controller.$('.accordion'));
                });
            });
        }
    }
});
