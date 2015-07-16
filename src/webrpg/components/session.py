# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""

from formencode import validators, All, Invalid
from sqlalchemy import and_

from webrpg.components.game import GameExistsValidator
from webrpg.components.user import UserExistsValidator
from webrpg.components.util import (get_current_user, EmberSchema)
from webrpg.models import (DBSession, Game, GameRole, Session, SessionRole)

class NewSessionSchema(EmberSchema):
    
    title = validators.UnicodeString(not_empty=True)
    game = All(validators.Int(not_empty=True),
               GameExistsValidator())


def new_session_param_transform(params):
    return {'title': params['title'],
            'game_id': params['game']}


def new_session_authorisation(request, params):
    user = get_current_user(request)
    if user:
        dbsession = DBSession()
        game = dbsession.query(Game).join(Game.roles).filter(and_(Game.id == params['game_id'],
                                                                  GameRole.user_id == user.id,
                                                                  GameRole.role == 'owner')).first()
        if game:
            return True
        else:
            return False
    else:
        return False


class SessionExistsValidator(validators.FancyValidator):
    
    messages = {'missing': 'The given session does not exist'}
    
    def _validate_python(self, value, state):
        if not state.dbsession.query(Session).filter(Session.id == value).first():
            raise Invalid(self.message('missing', state), value, state)


class NewSessionRoleSchema(EmberSchema):
    
    role = validators.UnicodeString(not_empty=True)
    user = All(validators.Int(not_empty=True),
               UserExistsValidator())
    session = All(validators.Int(not_empty=True),
                  SessionExistsValidator())


def new_session_role_param_transform(params):
    return {'role': params['role'],
            'user_id': params['user'],
            'session_id': params['session']}


MODELS = {'session': {'class': Session,
                      'new': {'schema': NewSessionSchema,
                              'authentication': True,
                              'authorisation': new_session_authorisation,
                              'param_transform': new_session_param_transform},
                      'list': {'authenticate': True},
                      'item': {'authenticate': True}},
          'sessionRole': {'class': SessionRole,
                          'new': {'schema': NewSessionRoleSchema,
                                  'authentication': True,
                                  'param_transform': new_session_role_param_transform},
                          'list': {'authenticate': True},
                          'item': {'authenticate': True}}}
