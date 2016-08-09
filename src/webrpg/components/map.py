# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""

from formencode import validators
from sqlalchemy import Column, Integer, ForeignKey, Unicode, UnicodeText
from sqlalchemy.orm import relationship

from webrpg.components import register_component
from webrpg.models import (Base, JSONAPIMixin)
from webrpg.util import JSONAPISchema, DynamicSchema


class Map(Base, JSONAPIMixin):

    __tablename__ = 'maps'

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.id', name='maps_session_id_fk'))
    title = Column(Unicode(255))
    map = Column(UnicodeText)
    fog = Column(UnicodeText)

    session = relationship('Session')

    __create_schema__ = JSONAPISchema('maps',
                                      attribute_schema=DynamicSchema({'title': validators.UnicodeString(not_empty=True)}),
                                      relationship_schema=DynamicSchema({'session': {'data': {'type': validators.OneOf(['sessions'],
                                                                                                                       not_empty=True),
                                                                                              'id': validators.Number}}}))
    __update_schema__ = JSONAPISchema('maps',
                                      attribute_schema=DynamicSchema({'title': validators.UnicodeString(),
                                                                      'map': validators.UnicodeString(),
                                                                      'fog': validators.UnicodeString()}))

    __json_attributes__ = ['title', 'map', 'fog']
    __json_relationships__ = ['session']

    def allow(self, user, action):
        return True


register_component('maps', Map, actions=['new', 'list', 'item', 'update'])
