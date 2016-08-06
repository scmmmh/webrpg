import hashlib
import inflection
import json
import random
import re

from copy import deepcopy
from formencode import Invalid
from sqlalchemy import (Column, Integer, Unicode, UnicodeText, ForeignKey)
from sqlalchemy.ext.declarative import (declarative_base)
from sqlalchemy.orm import (scoped_session, sessionmaker, relationship)
from zope.sqlalchemy import ZopeTransactionExtension

from webrpg.components import COMPONENTS
from webrpg.calculator import (tokenise, add_variables, infix_to_postfix, calculate, process_unary)
from webrpg.util import State

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


def convert_keys(data):
    if isinstance(data, dict):
        return dict([(k.replace('-', '_'), convert_keys(v)) for (k, v) in data.items()])
    elif isinstance(data, list):
        return [convert_keys(i) for i in data]
    else:
        return data


class JSONAPIMixin(object):

    @classmethod    
    def from_dict(self, data, dbsession):
        if hasattr(self, '__create_schema__'):
            data = self.__create_schema__.to_python(convert_keys(data),
                                                    State(dbsession=dbsession))
            obj = self()
            if 'relationships' in data:
                for key, value in data['relationships'].items():
                    if hasattr(obj, key):
                        if isinstance(value['data'], dict):
                            rel_class = COMPONENTS[value['data']['type']]['class']
                            rel = dbsession.query(rel_class).filter(rel_class.id == value['data']['id']).first()
                            if rel:
                                setattr(obj, key, rel)
                            else:
                                raise Invalid('Relationship target "%s" with id "%s" does not exist' % (value['data']['type'], value['data']['id']), value, None)
            if 'attributes' in data:
                for key, value in data['attributes'].items():
                    if hasattr(obj, key):
                        setattr(obj, key, value)
            return obj
        else:
            return None

    def as_dict(self, request=None, depth=1):
        data = {'id': self.id,
                'type': self.__class__.__name__}
        # Set plain attributes
        if hasattr(self, '__json_attributes__'):
            data['attributes'] = {}
            for attr_name in self.__json_attributes__:
                data['attributes'][attr_name.replace('_', '-')] = getattr(self, attr_name)
        # Set computed attributes
        if hasattr(self, '__json_computed__'):
            if 'attributes' not in data:
                data['attributes'] = {}
            for attr_name in self.__json_computed__:
                data['attributes'][attr_name.replace('_', '-')] = getattr(self, attr_name)(request)
        # Set relationships
        if hasattr(self, '__json_relationships__'):
            data['relationships'] = {}
            for rel_name in self.__json_relationships__:
                data['relationships'][rel_name.replace('_', '-')] = {'data': []}
                try:
                    for rel in getattr(self, rel_name):
                        if rel and rel.allow(request.current_user, 'view'):
                            data['relationships'][rel_name.replace('_', '-')]['data'].append({'id': rel.id,
                                                                                              'type': rel.__class__.__name__})
                except:
                    rel = getattr(self, rel_name)
                    if rel and rel.allow(request.current_user, 'view'):
                        data['relationships'][rel_name.replace('_', '-')]['data'] = {'id': rel.id,
                                                                                     'type': rel.__class__.__name__}
                if not data['relationships'][rel_name.replace('_', '-')]['data']:
                    del data['relationships'][rel_name.replace('_', '-')]
        included = []
        # Handle included data
        if depth > 0 and hasattr(self, '__json_relationships__'):
            for rel_name in self.__json_relationships__:
                if inflection.pluralize(rel_name) == rel_name:
                    for rel in getattr(self, rel_name):
                        if rel and rel.allow(request.current_user, 'view'):
                            rel_data, rel_included = rel.as_dict(request=request,
                                                                 depth=depth - 1)
                            included.append(rel_data)
                            if rel_included:
                                included.extend(rel_included)
                else:
                    rel = getattr(self, rel_name)
                    if rel and rel.allow(request.current_user, 'view'):
                        rel_data, rel_included = rel.as_dict(request=request,
                                                             depth=depth - 1)
                        included.append(rel_data)
                        if rel_included:
                            included.extend(rel_included)
        return data, included


class SessionRole(Base):
    
    __tablename__ = 'sessions_roles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', name='session_roles_user_id_fk'))
    session_id = Column(Integer, ForeignKey('sessions.id', name='sessions_roles_session_id_fk'))
    role = Column(Unicode(255))
    
    def as_dict(self):
        return {'id': self.id,
                'user': self.user_id,
                'session': self.session_id,
                'role': self.role}


class Map(Base):

    __tablename__ = 'maps'

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.id', name='maps_session_id_fk'))
    title = Column(Unicode(255))
    map = Column(UnicodeText)
    fog = Column(UnicodeText)

    session = relationship('Session')

    def as_dict(self):
        return {'id': self.id,
                'session': self.session_id,
                'title': self.title,
                'map': self.map,
                'fog': self.fog}
