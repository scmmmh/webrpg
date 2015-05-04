import DS from 'ember-data';

export default DS.Model.extend({
    label: DS.attr(),
    character_sheet: DS.attr()
});
