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
            if 'attributes' in data:
                for key, value in data['attributes'].items():
                    if hasattr(obj, key):
                        setattr(obj, key, value)
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
                data['relationships'][rel_name] = {'data': []}
                try:
                    for rel in getattr(self, rel_name):
                        if rel:
                            data['relationships'][rel_name]['data'].append({'id': rel.id,
                                                                            'type': rel.__class__.__name__})
                except:
                    rel = getattr(self, rel_name)
                    if rel:
                        data['relationships'][rel_name]['data'] = {'id': rel.id,
                                                                   'type': rel.__class__.__name__}
                if not data['relationships'][rel_name]['data']:
                    del data['relationships'][rel_name]
        included = []
        # Handle included data
        if depth > 0 and hasattr(self, '__json_relationships__'):
            for rel_name in self.__json_relationships__:
                if inflection.pluralize(rel_name) == rel_name:
                    for rel in getattr(self, rel_name):
                        if rel:
                            rel_data, rel_included = rel.as_dict(request=request,
                                                                 depth=depth - 1)
                            included.append(rel_data)
                            if rel_included:
                                included.extend(rel_included)
                else:
                    rel = getattr(self, rel_name)
                    if rel:
                        rel_data, rel_included = rel.as_dict(request=request,
                                                             depth=depth - 1)
                        included.append(rel_data)
                        if rel_included:
                            included.extend(rel_included)
        return data, included


class Session(Base):
    
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.id', name='sessions_game_id_fk'))
    title = Column(Unicode(255))
    dice_roller = Column(Unicode(255))
    
    game = relationship('Game')
    roles = relationship('SessionRole')
    maps = relationship('Map')
    chat_messages = relationship('ChatMessage', order_by='ChatMessage.id')
    
    def as_dict(self):
        return {'id': self.id,
                'title': self.title,
                'dice_roller': self.dice_roller,
                'game': self.game_id,
                'roles': [sr.id for sr in self.roles],
                'maps': [m.id for m in self.maps]}


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


class ChatMessage(Base):
    
    __tablename__ = 'chat_messages'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', name='chat_messages_user_id_fk'))
    session_id = Column(Integer, ForeignKey('sessions.id', name='chat_messages_session_id_fk'))
    message = Column(UnicodeText)
    filters = Column(Unicode(255))
    
    user = relationship('User')
    session = relationship('Session')
    
    def as_dict(self):
        return {'id': self.id,
                'user': self.user_id,
                'session': self.session_id,
                'message': self.message}


class Character(Base):

    __tablename__ = 'characters'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', name='characters_user_id_fk'))
    game_id = Column(Integer, ForeignKey('games.id', name='characters_game_id_fk'))
    attr = Column(UnicodeText)
    rule_set = Column(Unicode(255))

    def as_dict(self):
        from webrpg.components.rule_set import RULE_SETS
        attrs = json.loads(self.attr) if self.attr else {}
        rule_set = deepcopy(RULE_SETS[self.rule_set]) if self.rule_set else {}
        stats = []
        if 'stats' in rule_set:
            for source_table in rule_set['stats']:
                stat_table = {'id': '%s.%s' % (self.id, source_table['id']),
                              'title': source_table['title'],
                              'rows': []}
                if 'columns' in source_table:
                    stat_table['columns'] = deepcopy(source_table['columns'])
                for source_row in source_table['rows']:
                    row_id = '%s.%s.%s._row' % (self.id, source_table['id'], source_row['id'])
                    if 'multirow' in source_row and source_row['multirow']:
                        if '%s.%s._ids' % (source_table['id'], source_row['id']) in attrs:
                            multirow_ids = attrs['%s.%s._ids' % (source_table['id'], source_row['id'])]
                            multirow_ids.append(max(multirow_ids) + 1)
                        else:
                            multirow_ids = [0]
                    else:
                        multirow_ids = [None]
                    for idx, multirow_id in enumerate(multirow_ids):
                        if 'multirow' in source_row and source_row['multirow']:
                            stat_row = {'id': row_id % multirow_id,
                                        'columns': []}
                            if 'title' in source_row:
                                stat_row['title'] = '%i' % (idx + 1)
                        else:
                            stat_row = {'id': row_id,
                                        'columns': []}
                            if 'title' in source_row:
                                stat_row['title'] = source_row['title']
                        for source_column in source_row['columns']:
                            if 'multirow' in source_row and source_row['multirow']:
                                column_id = source_column['id'] % (multirow_id,)
                            else:
                                column_id = source_column['id']
                            stat_column = {'id': '%s.%s.%s' % (self.id, source_table['id'], column_id),
                                       'data_type': source_column['data_type'],
                                       'editable': source_column['editable'],
                                       'value': None}
                            if 'options' in source_column:
                                stat_column['options'] = source_column['options']
                            if 'formula' in source_column:
                                if 'multirow' in source_row:
                                    formula = source_column['formula'] % {'rowid': multirow_id}
                                else:
                                    formula = source_column['formula']
                                tokens = add_variables(tokenise(formula), attrs)
                                total = calculate(infix_to_postfix(tokens))
                                stat_column['value'] = total
                                attrs['%s.%s' % (source_table['id'], column_id)] = total
                            else:
                                key = '%s.%s' % (source_table['id'], column_id)
                                if key in attrs:
                                    stat_column['value'] = attrs[key]
                            stat_row['columns'].append(stat_column)
                        for stat_column, source_column in zip(stat_row['columns'], source_row['columns']):
                            if 'action' in source_column:
                                if 'action_title' in source_column:
                                    action_title = source_column['action_title']
                                else:
                                    action_title = source_row['title']
                                if 'multirow' in source_row and source_row['multirow']:
                                    action = source_column['action'] % {'rowid': multirow_id}
                                    action_title = action_title % {'rowid': multirow_id}
                                else:
                                    action = source_column['action']
                                stat_column['action'] = ' '.join([t[1] for t in process_unary(add_variables(tokenise(action), attrs))])
                                stat_column['action_title'] = ' '.join([t[1] for t in process_unary(add_variables(tokenise(action_title), attrs))])
                        if 'action' in source_row:
                            if 'action_title' in source_row:
                                action_title = source_row['action_title']
                            else:
                                action_title = source_row['title']
                            if 'multirow' in source_row and source_row['multirow']:
                                action = source_row['action'] % {'rowid': multirow_id}
                                action_title = action_title % {'rowid': multirow_id}
                            else:
                                action = source_row['action']
                            if 'action_calculate' in source_row and source_row['action_calculate']:
                                calc_match = re.search(re.compile('\$([^$]*)\$'), action)
                                while calc_match:
                                    if calc_match.group(0).strip() == '':
                                        break
                                    action = re.sub(re.compile('\$([^$]*)\$'),
                                                    str(calculate(infix_to_postfix(add_variables(tokenise(calc_match.group(1)), attrs)))),
                                                    action,
                                                    count=1)
                                    calc_match = re.search(re.compile('\$([^$]*)\$'), action)
                                stat_row['action'] = action
                            else:
                                stat_row['action'] = ' '.join([t[1] for t in process_unary(add_variables(tokenise(action), attrs))])
                            stat_row['action_title'] = ' '.join([t[1] for t in process_unary(add_variables(tokenise(action_title), attrs))])
                        stat_table['rows'].append(stat_row)
                stats.append(stat_table)
        title = 'Unnamed'
        if 'title' in rule_set and rule_set['title'] in attrs:
            title = attrs[rule_set['title']]
        return {'id': self.id,
                'title': title,
                'user': self.user_id,
                'game': self.game_id,
                'ruleSet': self.rule_set,
                'stats': stats}


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
