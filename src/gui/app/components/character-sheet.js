import Ember from 'ember';

export default Ember.Component.extend({
    classNames: ['clearfix'],
    actions: {
        select_tab: function(panel_id) {
            var panel = Ember.$('#' + panel_id);
            var open = panel.hasClass('active');
            panel.parent().parent().find('div.content').removeClass('active');
            if(!open) {
                panel.addClass('active');
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
