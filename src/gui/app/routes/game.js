import Ember from 'ember';

export default Ember.Route.extend({
    model: function(params) {
        var promise = this.store.find('game', params.gid);
        promise.then(function(game) {
            game.get('roles').then(function(roles) {
                roles.forEach(function(role) {
                    if(role.get('role') === 'owner') {
                        role.get('user').then(function(user) {
                            if(user.get('id') == sessionStorage.getItem('webrpg-userid')) { // jshint ignore:line
                                game.set('owned', true); 
                            } 
                        });
                    }
                });
            });
            game.get('sessions').then(function(sessions) {
               sessions.forEach(function(session) {
                  session.get('roles').then(function(roles) {
                      roles.forEach(function(role) {
                         role.get('user').then(function(user) {
                             if(user.get('id') == sessionStorage.getItem('webrpg-userid')) { // jshint ignore:line
                                 session.set('joined', true);
                             }
                         }); 
                      });
                  });
               });
            });
        });
        return promise;
    }
});
