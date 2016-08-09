import DS from 'ember-data';

export default DS.JSONAPISerializer.extend({
    serializeAttribute: function(snapshot, json, key, attributes) {
        if(snapshot.changedAttributes()[key] || snapshot.record.get('isNew')) {
            return this._super(snapshot, json, key, attributes);
        } else {
            return;
        }
    }
});
