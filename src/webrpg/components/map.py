# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""

from formencode import validators, All, Invalid
from sqlalchemy import and_

from webrpg.components.game import Game, GameRole
from webrpg.components.session import Session
from webrpg.models import (DBSession, Map)
from webrpg.util import (EmberSchema)


class NewMapSchema(EmberSchema):
    
    title = validators.UnicodeString(not_empty=True)


def new_map_param_transform(params):
    return {'title': params['title'],
            'session_id': params['session'],
            'map': '',
            'fog': ''}


def new_map_authorisation(request, params):
    user = get_current_user(request)
    if user:
        dbsession = DBSession()
        #game = dbsession.query(Game).join(Game.roles, Session.game).filter(and_(Session.id == params['session_id'],
        #                                                                        GameRole.user_id == user.id,
        #                                                                        GameRole.role == 'owner')).first()
        game = True
        if game:
            return True
        else:
            return False
    else:
        return False


class UpdateMapSchema(EmberSchema):
    
    title = validators.UnicodeString(not_empty=True)
    map = validators.UnicodeString()
    fog = validators.UnicodeString()


def update_map_param_transform(map, params):
    return {'title': params['title'],
            'session_id': params['session'],
            'map': params['map'] if params['map'] else map.map,
            'fog': params['fog'] if params['fog'] else map.fog}


MODELS = {'map': {'class': Map,
                      'new': {'schema': NewMapSchema,
                              'authentication': True,
                              'authorisation': new_map_authorisation,
                              'param_transform': new_map_param_transform},
                      'list': {'authenticate': True},
                      'item': {'authenticate': True},
                      'update': {'authenticate': True,
                                 'schema': UpdateMapSchema,
                                 'param_transform': update_map_param_transform},}}
