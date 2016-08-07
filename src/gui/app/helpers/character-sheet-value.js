import Ember from 'ember';

export function characterSheetValue(params) {
    if(params[0] === 'string') {
        return params[1];
    } else if(params[0] === 'number') {
        if(params[1] > 0) {
            return '+' + params[1];
        } else {
            return params[1];
        }
    } else if(params[0] === 'boolean') {
        if(params[1]) {
            return Ember.String.htmlSafe('<span class="fi-check"></span>');
        } else {
            return '';
        }
    } else if(params[0] === 'text') {
        var text = params[1].split('\n');
        var result = [];
        for(var idx = 0; idx < text.length; idx++) {
            result.push(Ember.Handlebars.Utils.escapeExpression(text[idx]) + '<br />');
        }
        return Ember.String.htmlSafe(result.join('\n'));
    } else if(params[0] === 'option') {
        return params[1];
    }
    return params[1];
}

export default Ember.Helper.helper(characterSheetValue);
