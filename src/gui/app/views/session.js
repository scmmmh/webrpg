import Ember from 'ember';

export default Ember.View.extend({
    chat_message_observer: function() {
        Ember.run.scheduleOnce('afterRender', this, this.chat_message_scroll_update);
    }.observes('controller.model.chats.[]'),
    chat_message_scroll_update: function() {
        var messages = this.$('.messages');
        var scrollTop = messages.scrollTop();
        var innerHeight = messages.innerHeight();
        var last_top = messages.children(':last-child()').position().top;
        if(scrollTop + innerHeight / 2 > last_top) {
            this.$('.messages').scrollTop(scrollTop + 1000);
        }
    }
});
