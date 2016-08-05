# -*- coding: utf-8 -*-
"""
###########################################
Handles all game-session model interactions
###########################################

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""

from formencode import validators
from sqlalchemy import Column, Integer, Unicode, ForeignKey
from sqlalchemy.orm import relationship

from webrpg.components import register_component
from webrpg.models import (Base, JSONAPIMixin)
from webrpg.util import (JSONAPISchema, DynamicSchema)


class Session(Base, JSONAPIMixin):
    """The :class:`~webrpg.components.session.Session` represents a single gaming
    session for a :class:`~webrpg.components.game.Game`. It holds the following
    attributes: "title", "dice_roller".
    """

    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.id', name='sessions_game_id_fk'))
    title = Column(Unicode(255))
    dice_roller = Column(Unicode(255))

    game = relationship('Game')
    maps = relationship('Map')
    chat_messages = relationship('ChatMessage', order_by='ChatMessage.id')

    __create_schema__ = JSONAPISchema('sessions',
                                      attribute_schema=DynamicSchema({'title': validators.UnicodeString(not_empty=True),
                                                                      'dice_roller': validators.OneOf(['d20', 'eote'],
                                                                                                      not_empty=True)}),
                                      relationship_schema=DynamicSchema({'game': {'data': {'type': validators.OneOf(['games'],
                                                                                                                    not_empty=True),
                                                                                           'id': validators.Number}}}))

    __json_attributes__ = ['title', 'dice_roller']
    __json_relationships__ = ['game', 'chat_messages']

    def allow(self, user, action):
        return True


register_component('sessions', Session, actions=['new', 'item'])
