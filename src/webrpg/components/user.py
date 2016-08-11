# -*- coding: utf-8 -*-
"""
###########################################
Handles all user-related model interactions
###########################################

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""
import hashlib
import random

from formencode import validators, schema, All, Invalid
from pyramid.httpexceptions import HTTPClientError
from pyramid.view import view_config
from sqlalchemy import (Column, Integer, Unicode, event)

from webrpg.components import register_component
from webrpg.models import DBSession, Base, JSONAPIMixin
from webrpg.util import State, BaseSchema, JSONAPISchema, invalid_to_error_list, raise_json_exception


class EmailExistsValidator(validators.FancyValidator):
    """Validator that checks whether the given e-mail address exists in the
    database. Requires a :class:`~webrpg.util.State` object with the "dbsession"
    attribute set to a valid database session"""

    messages = {'existing': 'A user with this e-mail address already exists'}

    def _convert_to_python(self, value, state):
        return value.lower()

    def _validate_python(self, value, state):
        user = state.dbsession.query(User).filter(User.email == value).first()
        if user and (not hasattr(state, 'userid') or user.id != state.userid):
            raise Invalid(self.message('existing', state), value, state)


class NewUserSchema(BaseSchema):
    """Schema for validating a new :class:`~webrpg.components.user.User`. Required
    fields are "email", "display_name", and "password".
    """

    email = All(validators.Email(not_empty=True), EmailExistsValidator())
    display_name = validators.UnicodeString(not_empty=True)
    password = validators.UnicodeString(not_empty=True)


class User(Base, JSONAPIMixin):
    """The :class:`~webrpg.components.user.User` represents any user in the system.
    It has the following attributes: "id", "email", "salt", "password", "display_name".
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(Unicode(255), unique=True, index=True)
    salt = Column(Unicode(255))
    password = Column(Unicode(255))
    display_name = Column(Unicode(64))

    __create_schema__ = JSONAPISchema('users', attribute_schema=NewUserSchema())

    __json_attributes__ = ['email', 'display_name']

    def password_matches(self, password):
        password = hashlib.sha512(('%s$$%s' % (self.salt, password)).encode('utf8')).hexdigest()
        return password == self.password

    def allow(self, user, action):
        """Check if the given :class:`~webrpg.components.user.User` is allowed
        to undertake the given ``action``."""
        return True


@event.listens_for(User.password, 'set', retval=True)
def hash_password(target, value, old_value, initiator):
    """Event listener that automatically hashes the password if it is changed."""
    target.salt = ''.join(chr(random.randint(32, 127)) for _ in range(32))
    return hashlib.sha512(('%s$$%s' % (target.salt, value)).encode('utf8')).hexdigest()


class PasswordValidator(schema.FancyValidator):
    """Validator that checks if the given ``{email: '', password: ''}`` dict matches
    a :class:`~webrpg.components.user.User`."""

    messages = {'nologin': 'No user exists with the given e-mail address or the password is incorrect'}

    def _convert_to_python(self, value, state):
        value['email'] = value['email'].lower()
        return value

    def _validate_python(self, value, state):
        user = state.dbsession.query(User).filter(User.email == value['email'].lower()).first()
        if user:
            if not user.password_matches(value['password']):
                raise Invalid(self.message('nologin', state), value, state)
        else:
            raise Invalid(self.message('nologin', state), value, state)


class LoginUserSchema(schema.Schema):
    """Schema for validating login attempts."""

    email = validators.Email(not_empty=True)
    password = validators.UnicodeString(not_empty=True)

    chained_validators = [PasswordValidator()]


@view_config(route_name='login', renderer='json')
def login(request):
    """Route handler for the special "login" route."""
    dbsession = DBSession()
    try:
        params = LoginUserSchema().to_python(request.POST, State(dbsession=dbsession))
        user = dbsession.query(User).filter(User.email == params['email']).first()
        return {'user': user.as_dict()[0]}
    except Invalid as e:
        raise_json_exception(HTTPClientError, body=invalid_to_error_list(e))


# Register the user as a component in the system
register_component(User, actions=['new', 'item'])
