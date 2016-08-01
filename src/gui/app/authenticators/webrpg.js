import Ember from 'ember';
import RSVP from 'rsvp';
import Base from 'ember-simple-auth/authenticators/base';

export default Base.extend({
  restore(auth_data) {
      return new RSVP.Promise(function(resolve, reject) {
          Ember.$.ajax('/api/users/login', {
              'method': 'POST',
              'dataType': 'json',
              'data': {
                  email: auth_data.email,
                  password: auth_data.password
              }
          }).then(function(data) {
              resolve({
                  'email': auth_data.email,
                  'userid': data.user.id,
                  'password': auth_data.password
              });
          }, function() {
              reject();
          });
      });
  },
  authenticate(email, password) {
      return new RSVP.Promise(function(resolve, reject) {
          Ember.$.ajax('/api/users/login', {
              'method': 'POST',
              'dataType': 'json',
              'data': {
                  email: email,
                  password: password
              }
          }).then(function(data) {
              resolve({
                  'email': email,
                  'userid': data.user.id,
                  'password': password
              });
          }, function(jqXHR) {
              reject(jqXHR.responseJSON);
          });
      });
  }
});