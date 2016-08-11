/* global createjs */
import Ember from 'ember';
import ApplicationRouteMixin from 'ember-simple-auth/mixins/application-route-mixin';

export default Ember.Route.extend(ApplicationRouteMixin, {
    init: function() {
        this._super(...arguments);
        createjs.Sound.registerSound("assets/notification.mp3", "notification");
    }
});
