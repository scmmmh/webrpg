import Ember from 'ember';

export function formatChatMessage(params) {
    var parts = params[0];
    var text = [];
    for(var idx = 0; idx < parts.length; idx++) {
        var part = [];
        if(parts[idx].type) {
            part.push('<');
            part.push(parts[idx].type);
            if(parts[idx].attrs) {
                for(var key in parts[idx].attrs) {
                    part.push(' ');
                    part.push(Ember.Handlebars.Utils.escapeExpression(key));
                    part.push('="');
                    part.push(Ember.Handlebars.Utils.escapeExpression(parts[idx].attrs[key]));
                    part.push('"');
                }
            }
            part.push('>');
            if(parts[idx].text) {
                part.push(Ember.Handlebars.Utils.escapeExpression(parts[idx].text));
            }
            part.push('</');
            part.push(parts[idx].type);
            part.push('>');
            text.push(part.join(''));
        }
    }
    return Ember.String.htmlSafe(text.join(''));
}

export default Ember.Helper.helper(formatChatMessage);
