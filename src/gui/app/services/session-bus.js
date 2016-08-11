import Ember from 'ember';

export default Ember.Service.extend({
    parts: {},
    
    register: function(action, component) {
        this.set('parts.' + action, component);
    },
    send: function() {
        var component = this.get('parts.' + arguments[0]);
        if(component) {
            component.send(arguments[0], ...Array.prototype.slice.call(arguments, 1));
        }
    }
});
