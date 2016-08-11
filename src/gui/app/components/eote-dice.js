import Ember from 'ember';

export default Ember.Component.extend({
    bus: Ember.inject.service('session-bus'),
    addressee: '',
    title: '',
    boost: 0,
    ability: 0,
    proficiency: 0,
    setback: 0,
    difficulty: 0,
    challenge: 0,
    force: 0,
    
    init: function() {
        this._super(...arguments);
        this.get('bus').register('setDice', this);
    },
    actions: {
        setDice: function(title, diceString) {
            this.set('title', title);
            this.set('boost', 0);
            this.set('ability', 0);
            this.set('proficiency', 0);
            this.set('setback', 0);
            this.set('difficulty', 0);
            this.set('challenge', 0);
            this.set('force', 0);
            diceString = diceString.toLowerCase();
            for(var idx = 0; idx < diceString.length; idx++) {
                if(diceString[idx + 1] === 'b') {
                    this.set('boost', diceString[idx]);
                } else if(diceString[idx + 1] === 'a') {
                    this.set('ability', diceString[idx]);
                } else if(diceString[idx + 1] === 'p') {
                    this.set('proficiency', diceString[idx]);
                } else if(diceString[idx + 1] === 's') {
                    this.set('setback', diceString[idx]);
                } else if(diceString[idx + 1] === 'd') {
                    this.set('difficulty', diceString[idx]);
                } else if(diceString[idx + 1] === 'c') {
                    this.set('challenge', diceString[idx]);
                } else if(diceString[idx + 1] === 'f') {
                    this.set('force', diceString[idx]);
                }
            }
        },
        resetDice: function() {
            this.set('addressee', '');
            this.set('title', '');
            this.set('boost', 0);
            this.set('ability', 0);
            this.set('proficiency', 0);
            this.set('setback', 0);
            this.set('difficulty', 0);
            this.set('challenge', 0);
            this.set('force', 0);
        },
        rollDice: function() {
            var message = '';
            if(this.get('addressee')) {
                message = message + '@' + this.get('addressee') + ' ';
            }
            if(this.get('title')) {
                message = message + this.get('title') + ': ';
            }
            if(this.get('boost')) {
                message = message + this.get('boost') + 'B';
            }
            if(this.get('ability')) {
                message = message + this.get('ability') + 'A';
            }
            if(this.get('proficiency')) {
                message = message + this.get('proficiency') + 'P';
            }
            if(this.get('setback')) {
                message = message + this.get('setback') + 'S';
            }
            if(this.get('difficulty')) {
                message = message + this.get('difficulty') + 'D';
            }
            if(this.get('challenge')) {
                message = message + this.get('challenge') + 'C';
            }
            if(this.get('force')) {
                message = message + this.get('force') + 'F';
            }
            if(message !== '') {
                this.get('bus').send('sendChatMessage', message);
            }
        }
    }
});
