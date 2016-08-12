import Ember from 'ember';

export default Ember.Component.extend({
    bus: Ember.inject.service('session-bus'),
    addressee: '',
    title: '',
    count: 1,
    die: 'd20',
    modifier: 0,
    
    init: function() {
        this._super(...arguments);
        this.get('bus').register('setDice', this);
    },
    actions: {
        setDice: function(title, diceString) {
            this.set('title', title);
            if(diceString.indexOf('d') >= 0) {
                var count = diceString.substring(0, diceString.indexOf('d'));
                if(count !== '') {
                    this.set('count', count);
                }
                if(diceString.indexOf('+') >= 0) {
                    var die = diceString.substring(diceString.indexOf('d'), diceString.indexOf('+')).toLowerCase();
                    this.set('die', die.trim());
                    var modifier = diceString.substring(diceString.indexOf('+') + 1);
                    this.set('modifier', modifier.trim());
                } else {
                    var die = diceString.substring(diceString.indexOf('d')).toLowerCase();
                    this.set('die', die.trim());
                    this.set('modifier', 0);
                }
            }
        },
        resetDice: function() {
            this.set('addressee', '');
            this.set('title', '');
            this.set('count', 1);
            this.set('die', 'd20');
            this.set('modifier', 0);
        },
        rollDice: function() {
            var message = '';
            if(this.get('addressee')) {
                message = message + '@' + this.get('addressee') + ' ';
            }
            if(this.get('title')) {
                message = message + this.get('title') + ': ';
            }
            if(this.get('count') !== 1) {
                message = message + this.get('count');
            }
            message = message + this.get('die');
            if(this.get('modifier')) {
                if(this.get('modifier') > 0) {
                    message = message + '+' + this.get('modifier');
                } else {
                    message = message + this.get('modifier');
                }
            }
            if(message !== '') {
                this.get('bus').send('sendChatMessage', message);
            }
        }
    }
});
