import Ember from 'ember';

export default Ember.Controller.extend({
    add_new_map: false,
    map_cursor_size: 10,
    map_cursor_sizes: [5, 10, 20, 40, 80],
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
                Ember.$('#chat-message-input').focus();
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
                    ctx.clearRect(0, 0, 1024, 768);
                    ctx.drawImage(img, 0, 0);
                }
            }
        },
        'new-snapshot': function() {
            if(this.get('current_map')) {
                this.set('snapshot_submit_label', 'Take Snapshot');
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
                    of: Ember.$(window)
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
                var controller = this;
                controller.set('snapshot_submit_label', 'Taking Snapshot');
                window.Webcam.snap(function(uri) {
                    current_map.set('map', uri);
                    var fog = Ember.$('#fog-edit');
                    var ctx = fog[0].getContext('2d');
                    ctx.fillStyle = '#ffffff';
                    ctx.fillRect(0, 0, 1024, 768);
                    current_map.set('fog', fog[0].toDataURL());
                    controller.set('snapshot_submit_label', 'Uploading Snapshot');
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
        },
        'new-image': function() {
            if(this.get('current_map')) {
                this.set('image_submit_label', 'Upload Image');
                Ember.$('#image-ui').show();
                Ember.$('#image-ui form').get(0).reset();
                Ember.$('#image-ui .dialog').position({
                    my: 'center center',
                    at: 'center center',
                    of: Ember.$(window)
                });
            }
        },
        'cancel-image': function() {
            Ember.$('#image-ui').hide();
        },
        'upload-image': function() {
            var current_map = this.get('current_map');
            if(current_map) {
                var controller = this;
                controller.set('image_submit_label', 'Processing Image');
                var file = Ember.$('#image-ui input[type=file]').get(0).files[0];
                if(file) {
                    console.log(file);
                    var imageType = /^image\//;
                    if(imageType.test(file.type)) {
                        var reader = new FileReader();
                        reader.onload = function(event) {
                            var fog = Ember.$('#fog-edit');
                            var ctx = fog[0].getContext('2d');
                            current_map.set('map', event.target.result);
                            ctx.fillStyle = '#ffffff';
                            ctx.fillRect(0, 0, 1024, 768);
                            current_map.set('fog', fog[0].toDataURL());
                            controller.set('image_submit_label', 'Uploading Image');
                            current_map.save().then(function() {
                                Ember.$('#image-ui').hide();
                            });
                        };
                        reader.readAsDataURL(file);
                    } else {
                        controller.set('image_submit_label', 'Invalid Image');
                        setTimeout(function() {controller.set('image_submit_label', 'Upload Image');}, 3000);
                    }
                } else {
                    controller.set('image_submit_label', 'Invalid Image');
                    setTimeout(function() {controller.set('image_submit_label', 'Upload Image');}, 3000);
                }
            }
        },
        'set-cursor-size': function() {
            this.set('map_cursor_size', parseInt(Ember.$('#map-cursor-size').val()));
        }
    }
});
