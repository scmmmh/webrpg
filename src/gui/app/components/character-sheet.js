import Ember from 'ember';

export default Ember.Component.extend({
    classNames: ['clearfix'],
    actions: {
        'select-tab': function(tab_id) {
            this.set('selected-tab', tab_id);
        },
        'refresh-tabs': function(tab) {
            var selected_tab = this.get('selected-tab');
            if(selected_tab) {
                var element = tab.$();
                if(element.data('tab-id') === selected_tab) {
                    element.addClass('active').children('.content').addClass('active');
                }
            }
        },
        cs_start_edit: function(stat_column) {
            stat_column.set('editing', true);
        },
        cs_cancel_edit: function(item) {
            item.rollback();
            item.set('editing', false);
        },
        cs_save_edit: function(item, character) {
            character.save();
            item.set('editing', false);
        }
    }
});
