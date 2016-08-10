import Ember from 'ember';

export default Ember.Component.extend({
    tagName: 'ul',
    classNames: ['accordion'],
    attributeBindings: ['data-accordion', 'data-options'],
    'data-accordion': '',
    'data-options': '',
    
    didInsertElement: function() {
        this.$().foundation();
    }
});
