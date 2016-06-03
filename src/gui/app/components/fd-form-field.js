import Ember from 'ember';

export default Ember.Component.extend({
    tagName: 'label',
    error: undefined,
    classNameBindings: ['error:is-invalid-label'],
    errorLabelClass: Ember.computed('error', function() {
        if(this.get('error')) {
            return 'form-error is-visible';
        } else {
            return 'form-error';
        }
    })
});
