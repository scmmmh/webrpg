import hashlib
import random

from sqlalchemy import (Column, Integer, Unicode, UnicodeText, ForeignKey, event)
from sqlalchemy.ext.declarative import (declarative_base)
from sqlalchemy.orm import (scoped_session, sessionmaker, relationship)
from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class User(Base):
    """The :class:`~webrpg.models.User` represents any user in the system.
    """
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
