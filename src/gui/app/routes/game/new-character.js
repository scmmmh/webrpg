import Ember from 'ember';

export default Ember.Route.extend({
    model: function() {
        var promise = Ember.RSVP.hash({
           ruleSets: this.store.find('RuleSet'),
           parent: this.modelFor('game')
        });
        return promise;
    },
    renderTemplate: function() {
        this.render({outlet: 'new-character'});
    }
});
