# -*- coding: utf-8 -*-
"""
###########################################
Handles all game-related model interactions
###########################################

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""

from formencode import validators
from sqlalchemy import Column, Integer, Unicode, ForeignKey
from sqlalchemy.orm import relationship

from webrpg.components import register_component
from webrpg.models import Base, JSONAPIMixin
from webrpg.util import JSONAPISchema, DynamicSchema


class Game(Base, JSONAPIMixin):
    """The :class:`~webrpg.components.game.Game` represents a role-playing game
    with a number of :class:`~webrpg.components.user.User`,
    :class:`~webrpg.components.character.Character`,
    :class:`~webrpg.components.session.Session`.
    """

    __tablename__ = 'games'

    id = Column(Integer, primary_key=True)
    title = Column(Unicode(255))

    sessions = relationship('Session', order_by='desc(Session.id)')
    roles = relationship('GameRole')

    __create_schema__ = JSONAPISchema('games',
                                      attribute_schema=DynamicSchema({'title': validators.UnicodeString(not_empty=True)}))

    __json_attributes__ = ['title']
    __json_computed__ = ['joined', 'owned']
    __json_relationships__ = ['roles', 'sessions']

    def joined(self, request):
        """Check if the current :class:`~webrpg.components.user.User` has joined
        this :class:`~webrpg.components.game.Game`."""
        for role in self.roles:
            if request.current_user and role.user_id == request.current_user.id:
                return True
        return False

    def owned(self, request):
        """Check if the current :class:`~webrpg.components.user.User` is the
        owner of this :class:`~webrpg.components.game.Game`."""
        for role in self.roles:
            if request.current_user and role.role == 'owner' and role.user_id == request.current_user.id:
                return True
        return False


class GameRole(Base, JSONAPIMixin):
    """The :class:`~webrpg.components.game.GameRole` represents the role a
    :class:`~webrpg.components.user.User` has in a :class:`~webrpg.components.game.Game`.
    Roles supported are: "owner" and "player".
    """

    __tablename__ = 'games_roles'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', name='games_roles_user_id_fk'))
    game_id = Column(Integer, ForeignKey('games.id', name='games_roles_game_id_fk'))
    role = Column(Unicode(255))

    game = relationship('Game')
    user = relationship('User')

    __create_schema__ = JSONAPISchema('game-roles',
                                      attribute_schema=DynamicSchema({'role': validators.UnicodeString(not_empty=True)}),
                                      relationship_schema=DynamicSchema({'game': {'data': {'type': validators.OneOf(['games'],
                                                                                                                    not_empty=True),
                                                                                           'id': validators.Number}},
                                                                         'user': {'data': {'type': validators.OneOf(['users'],
                                                                                                                    not_empty=True),
                                                                                           'id': validators.Number}}}))
    __json_attributes__ = ['role']
    __json_computed__ = ['is_me']
    __json_relationships__ = ['game', 'user']

    def is_me(self, request):
        """Check if the current :class:`~webrpg.components.user.User` is the one linked to
        this this :class:`~webrpg.components.game.GameRole`.""" 
        if request.current_user and request.current_user.id == self.user_id:
            return True
        else:
            return False


register_component('games', Game, actions=['list', 'new', 'item'])
register_component('game-roles', GameRole, actions=['list', 'new', 'item'])
