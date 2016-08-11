import Ember from 'ember';

export default Ember.Controller.extend({
    session: Ember.inject.service('session'),
    bus: Ember.inject.service('session-bus'),
    cursorSize: 10,
    cursorMode: 'reveal',
    chatMessageAutoScroll: true,
    chatMessageSound: true,
    
    init: function() {
        this._super(...arguments);
        if(localStorage.getItem('webrpg.chatMessageAutoScroll') === 'false') {
            this.set('chatMessageAutoScroll', false);
        }
        if(localStorage.getItem('webrpg.chatMessageSound') === 'false') {
            this.set('chatMessageSound', false);
        }
        this.get('bus').register('sendChatMessage', this);
    },
    actions: {
        sendChatMessage: function(text) {
            var controller = this;
            var user = controller.store.findRecord('user', controller.get('session.data.authenticated.userid'));
            user.then(function() {
                if(text !== '') {
                    var message = controller.store.createRecord('chatMessage', {
                        message: text,
                        user: user,
                        session: controller.get('model')
                    });
                    message.save();
                }
            });
        },
        csAction: function(type, title, content) {
            this.get('bus').send(type, title, content);
        },
        addMap: function() {
            var controller = this;
            controller.set('addingMap', true);
        },
        cancelMap: function() {
            var controller = this;
            controller.set('mapTitle', '');
            controller.set('addingMap', false);
        },
        saveMap: function() {
            var controller = this;
            var title = controller.get('mapTitle');
            if(title) {
                var map = controller.store.createRecord('map', {
                    title: title,
                    session: controller.get('model')
                });
                map.save().then(function() {
                    controller.set('mapTitle', '');
                    controller.set('addingMap', false);
                });
            }
        },
        reloadMap: function(map) {
            map.reload();
        },
        uploadSelectMap: function() {
            Ember.$('#mapFileUpload').click();
        },
        uploadMap: function(map) {
            var file = Ember.$('#mapFileUpload').get(0).files[0];
            if(file) {
                if(/^image\//.test(file.type)) {
                    map.set('saving', true);
                    map.set('map', '');
                    map.set('fog', '');
                    var reader = new FileReader();
                    reader.onload = function(event) {
                        map.set('map', event.target.result);
                    };
                    reader.readAsDataURL(file);
                }
            }
        },
        deleteMap: function(map) {
            var controller = this;
            if(confirm('Please confirm that you wish to delete this map')) {
                map.deleteRecord();
                map.save().then(function() {
                    controller.set('selectedMap', null);
                });
            }
        },
        selectMap: function(map) {
            var controller = this;
            if(controller.get('selectedMap')) {
                controller.set('selectedMap.active', false);
            }
            map.set('active', true);
            controller.set('selectedMap', map);
        },
        setCursorSize: function(size) {
            this.set('cursorSize', size);
        },
        setCursorMode: function(mode) {
            this.set('cursorMode', mode);
        },
        toggleChatMessageAutoScroll: function() {
            this.set('chatMessageAutoScroll', !this.get('chatMessageAutoScroll'));
            localStorage.setItem('webrpg.chatMessageAutoScroll', this.get('chatMessageAutoScroll'));
        },
        toggleChatMessageSound: function() {
            this.set('chatMessageSound', !this.get('chatMessageSound'));
            localStorage.setItem('webrpg.chatMessageSound', this.get('chatMessageSound'));
        }
    }
});
