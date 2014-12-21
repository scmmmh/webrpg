import Ember from 'ember';

export default Ember.Component.extend({
    tagName: 'nav',
    classNames: ['top-bar'],
    attributeBindings: ['role', 'data-topbar'],
    role: 'navigation',
    'data-topbar': 'data-topbar',
    initJS: function() {
        Ember.$(document).foundation('topbar', 'reflow');
    }.on('didInsertElement')
});
