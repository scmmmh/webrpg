import hashlib
import json
import random
import re

from copy import deepcopy
from sqlalchemy import (Column, Integer, Unicode, UnicodeText, ForeignKey, event)
from sqlalchemy.ext.declarative import (declarative_base)
from sqlalchemy.orm import (scoped_session, sessionmaker, relationship)
from zope.sqlalchemy import ZopeTransactionExtension

from webrpg.calculator import (tokenise, add_variables, infix_to_postfix, calculate, process_unary,
                               calculation_regexp)

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class User(Base):
    '''The :class:`~webrpg.models.User` represents any user in the system.
    '''
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(Unicode(255), unique=True, index=True)
    salt = Column(Unicode(255))
    password = Column(Unicode(255))
    display_name = Column(Unicode(64))
    
    def password_matches(self, password):
        password = hashlib.sha512(('%s$$%s' % (self.salt, password)).encode('utf8')).hexdigest()
        return password == self.password
    
    def as_dict(self):
        return {'id': self.id,
                'email': self.email,
                'display_name': self.display_name}


@event.listens_for(User.password, 'set', retval=True)
def hash_password(target, value, old_value, initiator):
    target.salt = ''.join(chr(random.randint(0, 127)) for _ in range(32))
    return hashlib.sha512(('%s$$%s' % (target.salt, value)).encode('utf8')).hexdigest()


class Game(Base):

    __tablename__ = 'games'

    id = Column(Integer, primary_key=True)
    title = Column(Unicode(255))
    
    sessions = relationship('Session', order_by='desc(Session.id)')
    roles = relationship('GameRole')
    
    def as_dict(self):
        return {'id': self.id,
                'title': self.title,
                'roles': [r.id for r in self.roles],
                'sessions': [s.id for s in self.sessions]}


class GameRole(Base):
    
    __tablename__ = 'games_roles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', name='games_roles_user_id_fk'))
    game_id = Column(Integer, ForeignKey('games.id', name='games_roles_game_id_fk'))
    role = Column(Unicode(255))
    
    def as_dict(self):
        return {'id': self.id,
                'user': self.user_id,
                'game': self.game_id,
                'role': self.role}


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
