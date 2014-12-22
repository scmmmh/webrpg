# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""

from formencode import validators, schema, All, Invalid
from sqlalchemy import and_

from webrpg.components.user import UserExistsValidator
from webrpg.components.util import (get_current_user, EmberSchema)
from webrpg.models import DBSession, Game, GameRole


class NewGameSchema(EmberSchema):
    
    title = validators.UnicodeString(not_empty=True)


def new_game_param_transform(params):
    return {'title': params['title']}


class GameExistsValidator(validators.FancyValidator):
    
    messages = {'missing': 'The given game does not exist'}
    
    def _validate_python(self, value, state):
        if not state.dbsession.query(Game).filter(Game.id == value).first():
            raise Invalid(self.message('missing', state), value, state)


class NewGameRoleSchema(EmberSchema):
    
    role = validators.UnicodeString(not_empty=True)
    user = All(validators.Int(not_empty=True),
               UserExistsValidator())
    game = All(validators.Int(not_empty=True),
               GameExistsValidator())


def new_game_role_param_transform(params):
    return {'role': params['role'],
            'user_id': params['user'],
            'game_id': params['game']}


def game_authorisation(request, params):
    user = get_current_user(request)
    dbsession = DBSession()
    if dbsession.query(GameRole).filter(and_(GameRole.user_id == user.id,
                                             GameRole.game_id == request.matchdict['iid'])).first():
        return True
    else:
        return False


MODELS = {'game': {'class': Game,
                   'new': {'schema': NewGameSchema,
                           'authentication': True,
                           'param_transform': new_game_param_transform},
                   'list': {'authenticate': True},
                   'item': {'authenticate': True,
                            'authorisation': game_authorisation}},
          'gameRole': {'class': GameRole,
                       'new': {'schema': NewGameRoleSchema,
                               'authentication': True,
                               'param_transform': new_game_role_param_transform},
                       'list': {'authenticate': True},
                       'item': {'authenticate': True}}}
