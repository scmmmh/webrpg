import Ember from 'ember';

export default Ember.Route.extend({
    model: function(params) {
        var promise = Ember.RSVP.hash({
            game: this.store.findRecord('game', params.gid),
            characters: this.store.query('character', {
                game_id: params.gid,
                user_id: sessionStorage.getItem('webrpg-userid')
            })
        });
        promise.then(function(data) {
            data.game.get('roles').then(function(roles) {
                roles.forEach(function(role) {
                    if(role.get('role') === 'owner') {
                        role.get('user').then(function(user) {
                            if(user.get('id') == sessionStorage.getItem('webrpg-userid')) { // jshint ignore:line
                                data.game.set('owned', true); 
                            } 
                        });
                    }
                });
            });
            data.game.get('sessions').then(function(sessions) {
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
