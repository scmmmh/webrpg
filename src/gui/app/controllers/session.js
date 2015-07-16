import Ember from 'ember';

export default Ember.Controller.extend({
    add_new_map: false,
    actions: {
        new_chat_message: function() {
            var controller = this;
            
            var message = controller.get('new_chat_message');
            if(message) {
                var session = controller.get('model').session;
                controller.store.find('User', sessionStorage.getItem('webrpg-userid')).then(function(user) {
                    var chat_message = controller.store.createRecord('ChatMessage', {
                        message: message,
                        user: user,
                        session: session
                    }); 
                    chat_message.save().then(function() {
                        controller.set('new_chat_message', ''); 
                    });
                });
            }
        },
        'stat-click': function(character, stat) {
            if(stat.get('has_action')) {
                if(this.get('model').characters.get('length') > 1) {
                    this.set('new_chat_message', character.get('title') + ' ' + stat.get('action_title') + ': ' + stat.get('action'));
                } else {
                    this.set('new_chat_message', stat.get('action_title') + ': ' + stat.get('action'));
                }
                $('#chat-message-input').focus();
            }
        },
        'new-map': function() {
            this.set('add_new_map', true);
        },
        'cancel-new-map': function() {
            this.set('add_new_map', false);
        },
        'create-new-map': function() {
            var controller = this;
            var title = controller.get('new_map_title');
            if(title && title !== '') {
                var map = controller.store.createRecord('Map', {
                   title: title,
                   session: controller.model.session
                });
                map.save().then(function() {
                    controller.set('add_new_map', false);
                    controller.set('new_map_title', '');
                });
            }
        },
        'select-map': function(map) {
            this.get('model').session.get('maps').forEach(function (old_map) {
               old_map.set('current', false);
            });
            map.set('current', true);
            this.set('current_map', map);
            if(this.get('model').session.get('game').get('owned')) {
                var fog = Ember.$('#fog-edit');
                var ctx = fog[0].getContext('2d');
                if(Ember.isNone(map.get('fog')) || map.get('fog') === '') {
                    ctx.fillStyle = '#ffffff';
                    ctx.fillRect(0, 0, 1024, 768);
                } else {
                    var img = document.createElement('img');
                    img.src = map.get('fog');
                    ctx.drawImage(img, 0, 0);
                }
            }
        },
        'new-snapshot': function() {
            if(this.get('current_map')) {
                window.Webcam.set({
                    width: 320,
                    height: 240,
                    dest_width: 1024,
                    dest_height: 768
                });
                window.Webcam.attach('#video');
                Ember.$('#snapshot-ui').show();
                Ember.$('#snapshot-ui .dialog').position({
                    my: 'center center',
                    at: 'center center',
                    of: $(window)
                });
            }
        },
        'cancel-snapshot': function() {
            window.Webcam.reset();
            Ember.$('#snapshot-ui').hide();
        },
        'upload-snapshot': function() {
            var current_map = this.get('current_map');
            if(current_map) {
                window.Webcam.snap(function(uri) {
                    current_map.set('map', uri);
                    var fog = Ember.$('#fog-edit');
                    var ctx = fog[0].getContext('2d');
                    ctx.fillStyle = '#ffffff';
                    ctx.fillRect(0, 0, 1024, 768);
                    current_map.set('fog', fog[0].toDataURL());
                    current_map.save().then(function() {
                        window.Webcam.reset();
                        Ember.$('#snapshot-ui').hide();
                    });
                });
            }
        },
        'update-fog': function() {
            var current_map = this.get('current_map');
            if(current_map) {
                var fog = Ember.$('#fog-edit');
                current_map.set('fog', fog[0].toDataURL());
                current_map.save();
            }
        }
    }
});
