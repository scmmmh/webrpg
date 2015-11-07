import Ember from 'ember';

export default Ember.Route.extend({
    model: function() {
        var promise = this.store.findAll('game');
        promise.then(function(games) {
            games.forEach(function(game) {
                game.get('roles').then(function(roles) {
                    roles.forEach(function(role) {
                        role.get('user').then(function(user) {
                            if(user.get('id') == sessionStorage.getItem('webrpg-userid')) { // jshint ignore:line
                                game.set('joined', true); 
                            } 
                        });
                    });
                });
            });
        });
        return promise;
    }
});
