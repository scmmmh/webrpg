import Ember from 'ember';

export default Ember.Component.extend({
    tagName: 'li',
    classNames: ['accordion-navigation'],
    attributeBindings: ['data-tab-id'],
    element_inserted: function() {
        this.sendAction('action', this);
    }.on('didInsertElement')
});
