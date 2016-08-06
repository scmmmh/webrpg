import Ember from 'ember';
import AuthenticatedRouteMixin from 'ember-simple-auth/mixins/authenticated-route-mixin';

export default Ember.Route.extend(AuthenticatedRouteMixin, {
    model: function(params) {
        var promise = this.store.findRecord('Game', params.gid);
        /*promise.then(function(game) {
            game.get('characters').forEach(function(character) {
                var stats = character.get('stats');
                for(var idx = 0; idx < stats.length; idx++) {
                    console.log(stats[idx].title);
                    if(stats[idx].columns) {
                    }
                    if(stats[idx].rows) {
                        for(var idx2 = 0; idx2 < stats[idx].rows.length; idx2++) {
                            console.log(stats[idx].rows[idx2].title);
                            for(var idx3 = 0; idx3 < stats[idx].rows[idx2].columns.length; idx3++) {
                                console.log(stats[idx].rows[idx2].columns[idx3]);
                            }
                        }
                    }
                }
            });
        });*/
        return promise;
    }
});
