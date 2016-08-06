import Ember from 'ember';

export default Ember.Component.extend({
    tagName: 'li',
    classNames: ['accordion-item'],
    attributeBindings: ['data-accordion-item'],
    'data-accordion-item': '',
    
    didInsertElement: function() {
        Ember.run.schedule('afterRender', function() {
            Foundation.reInit(Ember.$('.accordion-item').parent(''));
        });
    }
});
