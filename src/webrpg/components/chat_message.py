# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""

import random
import re

from formencode import validators, schema, All, Invalid

from webrpg.components.session import SessionExistsValidator
from webrpg.components.user import UserExistsValidator
from webrpg.components.util import (get_current_user, EmberSchema)
from webrpg.models import DBSession, ChatMessage

class NewChatMessageSchema(EmberSchema):
    
    message = validators.UnicodeString(not_empty=True)
    user = All(validators.Int(not_empty=True),
               UserExistsValidator())
    session = All(validators.Int(not_empty=True),
                  SessionExistsValidator())


def new_chat_message_authorisation(request, params):
    user = get_current_user(request)
    if user:
        return True
    else:
        return False


dice_regexp = re.compile(r'([0-9]*)[Dd]([0-9]+)')
calculation_regexp = re.compile(r'((?:(?:\(?[0-9]*[dD][0-9]+)|(?:\(?[0-9]+))(?:(?:[0-9]*[dD][0-9]+)|(?:[0-9]+)|(?:[+\-*/()])|\s+)*)')

def tokenise(string):
    tokens = []
    tmp = []
    for c in string:
        if c in ['+', '-', '*', '/']:
            if tmp:
                tokens.append(('val', ''.join(tmp).strip()))
                tmp = []
            tokens.append(('op', c))
        elif c in ['(', ')']:
            if tmp:
                tokens.append(('val', ''.join(tmp).strip()))
                tmp = []
            tokens.append(('bra', c))
        elif c == ' ':
            if tmp: 
                tokens.append(('val', ''.join(tmp).strip()))
                tmp = []
        else:
            tmp.append(c)
    if tmp:
        tokens.append(('val', ''.join(tmp).strip()))
    return tokens

def add_dice(tokens):
    new_tokens = []
    for token in tokens:
        if token[0] == 'val':
            match = re.match(dice_regexp, token[1])
            if match:
                if match.group(1):
                    new_tokens.append(('bra', '('))
                    count = int(match.group(1))
                    for i in range(0, count):
                        new_tokens.append(('val', str(random.randint(1, int(match.group(2))))))
                        if i < count - 1:
                            new_tokens.append(('op', '+'))
                    new_tokens.append(('bra', ')'))
                else:
                    new_tokens.append(('val', str(random.randint(1, int(match.group(2))))))
            else:
                new_tokens.append(token)
        else:
            new_tokens.append(token)
    return new_tokens

def op_preference(op):
    if op == '(':
        return -1
    elif op in ['*', '/']:
        return 1
    else:
        return 0
    
def infix_to_postfix(tokens):
    stack = []
    output = []
    for token in tokens:
        if token[0] == 'val':
            output.append(token)
        elif token[0] == 'op':
            if not stack:
                stack.append(token[1])
            else:
                if op_preference(stack[-1]) < op_preference(token[1]):
                    stack.append(token[1])
                else:
                    while stack and op_preference(stack[-1]) >= op_preference(token[1]):
                        output.append(('op', stack.pop()))
                    stack.append(token[1])
        elif token[0] == 'bra':
            if token[1] == '(':
                stack.append('(')
            elif token[1] == ')':
                token = stack.pop()
                while stack and token != '(':
                    output.append(('op', token))
                    token = stack.pop()
    while stack:
        output.append(('op', stack.pop()))
    return output

def calculate(tokens):
    stack = []
    for token in tokens:
        if token[0] == 'val':
            stack.append(int(token[1]))
        elif token[0] == 'op':
            b = stack.pop()
            a = stack.pop()
            if token[1] == '+':
                stack.append(a + b)
            elif token[1] == '-':
                stack.append(a - b)
            elif token[1] == '*':
                stack.append(a * b)
            elif token[1] == '/':
                stack.append(a / b)
    return stack.pop()

def new_chat_message_param_transform(params):
    message = params['message']
    calc_match = re.search(calculation_regexp, message)
    substitutions = []
    while calc_match:
        if calc_match.group(0).strip() == '':
            break
        tokens = add_dice(tokenise(calc_match.group(0)))
        total = calculate(infix_to_postfix(tokens))
        if calc_match.group(0).strip() == ' '.join([t[1] for t in tokens]).strip():
            substitutions.append(calc_match.group(0))
        else:
            if ' '.join([t[1] for t in tokens]).strip() == str(int(round(total))):
                substitutions.append('%s = %i ' % (calc_match.group(0),
                                                   int(round(total))))
            else:
                substitutions.append('%s = %s = %i ' % (calc_match.group(0),
                                                        ' '.join([t[1] for t in tokens]),
                                                        int(round(total))))
        message = re.sub(calculation_regexp, '%s', message, count=1)
        calc_match = re.search(calculation_regexp, message)
    return {'message': message % tuple(substitutions),
            'user_id': params['user'],
            'session_id': params['session']}

def chat_message_filter(request, query):
    def user_has_role(user, role_name, session):
        for role in session.roles:
            if role.user_id == user.id and role.role == role_name:
                return True
        return False
    def filter_specific(user, message):
        if message.user.id == user.id:
            return True
        else:
            match = re.search(r'@[a-zA-Z0-9_\-]+', message.message)
            if match:
                for match in re.findall(r'@([a-zA-Z0-9_\-]+)', message.message):
                    if match.lower() == 'all' or match.lower() == user.display_name.lower():
                        return True
                    elif match.lower().replace('-', ' ') == user.display_name.lower():
                        return True
                    elif match.lower() == 'gm' and user_has_role(user, 'owner', message.session):
                        return True
                    elif match.lower() == 'players' and user_has_role(user, 'player', message.session):
                        return True
                    #elif match.lower() == 'gm' and request.current_user.id == session.creator.id: 
                    #    return True
                    #elif match.lower() == 'players' and request.current_user.id != session.creator.id:
                    #    return True
                    #elif match.lower() == 'players' and request.current_user.id == session.creator.id:
                    #    return False
                return False
            else:
                return True
    user = get_current_user(request)
    return [m for m in query if filter_specific(user, m)]


def chat_message_refresh(request, min_id):
    dbsession = DBSession()
    return [cm.as_dict() for cm in chat_message_filter(request, dbsession.query(ChatMessage).filter(ChatMessage.id > min_id))]


MODELS = {'chatMessage': {'class': ChatMessage,
                          'new': {'schema': NewChatMessageSchema,
                                  'authenticate': True,
                                  'authorisation': new_chat_message_authorisation,
                                  'param_transform': new_chat_message_param_transform},
                          'list': {'authenticate': True,
                                   'filter': chat_message_filter},
                          'refresh': {'authenticate': True,
                                      'func': chat_message_refresh}}}
