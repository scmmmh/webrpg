# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""

from formencode import validators, schema, All, Invalid

from webrpg.models import User

class EmailExistsValidator(validators.FancyValidator):
    
    messages = {'existing': 'A user with this e-mail address already exists'}
    
    def _convert_to_python(self, value, state):
        return value.lower()
    
    def _validate_python(self, value, state):
        user = state.dbsession.query(User).filter(User.email == value).first()
        if user and (not hasattr(state, 'userid') or user.id != state.userid):
            raise Invalid(self.message('existing', state), value, state)


class NewUserSchema(schema.Schema):
    
    email = All(validators.Email(not_empty=True), EmailExistsValidator())
    display_name = validators.UnicodeString(not_empty=True)
    password = validators.UnicodeString(not_empty=True)


class UserExistsValidator(validators.FancyValidator):
    
    messages = {'missing': 'The given user does not exist'}
    
    def _validate_python(self, value, state):
        if not state.dbsession.query(User).filter(User.id == value).first():
            raise Invalid(self.message('missing', state), value, state)


MODELS = {'user': {'class': User,
                   'new': {'schema': NewUserSchema,
                           'authentication': False},
                   'list': {'authenticate': True},
                   'item': {'authenticate': True}}}
