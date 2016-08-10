import Ember from 'ember';

export default Ember.Component.extend({
    tagName: 'ul',
    classNames: ['accordion'],

    click: function(ev) {
        var link = $(ev.target);
        console.log(link);
        if(link.hasClass('accordion-title')) {
            ev.preventDefault();
            if(link.parent().hasClass('is-active')) {
                this.get('selectTab')('');
                link.parent().removeClass('is-active');
            } else {
                this.get('selectTab')(link.parent().data('accordion-item'));
                link.parent().addClass('is-active');
            }
        }
    }
});
