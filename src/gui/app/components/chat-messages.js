import Ember from 'ember';

export default Ember.Component.extend({
    bus: Ember.inject.service('session-bus'),
    classNames: ['chat'],
    addressee: '',
    message: '',
    
    init: function() {
        this._super(...arguments);
        this.get('bus').register('setChatMessage', this);
    },
    actions: {
        setChatMessage: function() {
            this.set('chatMessage', Array.join(arguments, ': '));
        },
        addChatMessage: function() {
            var message = '';
            if(this.get('addressee')) {
                message = message + '@' + this.get('addressee') + ' ';
            }
            message = message + this.get('message');
            this.get('bus').send('sendChatMessage', message);
            this.set('message', '');
        }
    }
});
