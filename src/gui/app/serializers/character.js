import DS from 'ember-data';

export default DS.RESTSerializer.extend(DS.EmbeddedRecordsMixin, {
    attrs: {
        game: {serialize: 'ids'},
        user: {serialize: 'ids'},
        ruleSet: {serialize: 'ids'},
        stats: {embedded: 'always'}
    },
    isNewSerializerAPI: true
});
