import hashlib
import json
import random

from copy import deepcopy
from sqlalchemy import (Column, Integer, Unicode, UnicodeText, ForeignKey, event)
from sqlalchemy.ext.declarative import (declarative_base)
from sqlalchemy.orm import (scoped_session, sessionmaker, relationship)
from zope.sqlalchemy import ZopeTransactionExtension

from webrpg.calculator import (tokenise, add_variables, infix_to_postfix, calculate)

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
    
    sessions = relationship('Session', order_by='Session.id')
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
    
    roles = relationship('SessionRole')
    chat_messages = relationship('ChatMessage', order_by='ChatMessage.id')
    
    def as_dict(self):
        return {'id': self.id,
                'title': self.title,
                'game': self.game_id,
                'roles': [sr.id for sr in self.roles]}


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
        attrs = json.loads(self.attr) if self.attr else {'basic.name': 'Mark',
                                                         'base.proficiency': 2,
                                                         'abilities.strength': 12,
                                                         'skills.acrobatics.proficient': True}
        rule_set = deepcopy(RULE_SETS[self.rule_set]) if self.rule_set else {}
        stats = []
        if 'stats' in rule_set:
            for source_table in rule_set['stats']:
                stat_table = {'id': '%s.%s' % (self.id, source_table['id']),
                              'title': source_table['title'],
                              'columns': deepcopy(source_table['columns']),
                              'rows': []}
                for source_row in source_table['rows']:
                    stat_row = {'id': '%s.%s.%s.row' % (self.id, source_table['id'], source_row['id']),
                                'title': source_row['title'],
                                'columns': []}
                    for source_column in source_row['columns']:
                        stat_column = {'id': '%s.%s.%s' % (self.id, source_table['id'], source_column['id']),
                                       'data_type': source_column['data_type'],
                                       'editable': source_column['editable'],
                                       'value': None}
                        if 'formula' in source_column:
                            tokens = add_variables(tokenise(source_column['formula']), attrs)
                            total = calculate(infix_to_postfix(tokens))
                            stat_column['value'] = total
                            attrs['%s.%s' % (source_table['id'], source_column['id'])] = total
                        else:
                            key = '%s.%s' % (source_table['id'], source_column['id'])
                            if key in attrs:
                                stat_column['value'] = attrs[key]
                        stat_row['columns'].append(stat_column)
                    stat_table['rows'].append(stat_row)
                stats.append(stat_table)
        return {'id': self.id,
                'user': self.user_id,
                'game': self.game_id,
                'ruleSet': self.rule_set,
                'stats': stats}
