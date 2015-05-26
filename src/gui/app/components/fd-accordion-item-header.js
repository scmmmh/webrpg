import Ember from 'ember';

export default Ember.Component.extend({
    tagName: 'a',
    actions: {
        'select-tab': function() {
            if(this.$().parent().hasClass('active')) {
                this.$().parent().removeClass('active').children('.content').removeClass('active');
                this.sendAction('action', null);
            } else {
                this.$().parent().siblings().removeClass('active').children('.content').removeClass('active');
                this.$().parent().addClass('active').children('.content').addClass('active');
                this.sendAction('action', this.get('target-id'));
            }
        }
    },
    element_inserted: function() {
        var component = this;
        this.$().on('click', function() {
            Ember.run(function() {
               Ember.run.schedule('actions', this, function() {
                   component.send('select-tab');
               });
            });
        });
    }.on('didInsertElement')
});
