# -*- coding: utf-8 -*-
"""
###################################################
Handles all chat-message-related model interactions
###################################################

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
import random
import re

from formencode import validators
from sqlalchemy import Column, Unicode, UnicodeText, Integer, ForeignKey, event
from sqlalchemy.orm import relationship

from webrpg.calculator import (calculation_regexp, add_dice, tokenise, calculate,
                               infix_to_postfix, process_unary)
from webrpg.components import register_component
from webrpg.models import Base, JSONAPIMixin, JSONUnicodeText
from webrpg.util import (JSONAPISchema, DynamicSchema)


class ChatMessage(Base, JSONAPIMixin):
    """The :class:`~webrpg.components.chat_message.ChatMessage` represents a single chat
    message. It has the following attributes: "user", "session", "message".

    Setting the "message" attribute automatically applies any dice rolls.
    """

    __tablename__ = 'chat_messages'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', name='chat_messages_user_id_fk'))
    session_id = Column(Integer, ForeignKey('sessions.id', name='chat_messages_session_id_fk'))
    message = Column(UnicodeText)
    formatted = Column(JSONUnicodeText)
    filters = Column(Unicode(255))

    user = relationship('User')
    session = relationship('Session')

    __create_schema__ = JSONAPISchema('chat-messages',
                                      attribute_schema=DynamicSchema({'message': validators.UnicodeString(not_empty=True)}),
                                      relationship_schema=DynamicSchema({'user': {'data': {'type': validators.OneOf(['users'],
                                                                                                                    not_empty=True),
                                                                                           'id': validators.Number}},
                                                                         'session': {'data': {'type': validators.OneOf(['sessions'],
                                                                                                                       not_empty=True),
                                                                                              'id': validators.Number}}}))

    __json_attributes__ = ['message', 'formatted']
    __json_relationships__ = [('user', True), 'session']

    def allow(self, user, action):
        """Check if the given :class:`~webrpg.components.user.User` is allowed
        to undertake the given ``action``."""
        if user:
            if self.user_id == user.id:
                return True
            else:
                if action == 'view':
                    match = re.search(r'@[a-zA-Z0-9_\-]+', self.message)
                    if match:
                        for match in re.findall(r'@([a-zA-Z0-9_\-]+)', self.message):
                            if match.lower() == 'all' or match.lower() == user.display_name.lower():
                                return True
                            elif match.lower().replace('-', ' ') == user.display_name.lower():
                                return True
                            elif match.lower() == 'gm' and self.session.game.has_role(user, 'owner'):
                                return True
                            elif match.lower() == 'players' and self.session.game.has_role(user, 'player'):
                                return True
                        return False
                    else:
                        return True
                else:
                    return False
        else:
            return False


@event.listens_for(ChatMessage.message, 'set')
def calculate_dicerolls(target, value, old_value, initiator):
    """Event listener that automatically handles the dice rolls."""
    tmp = format_urls(value)
    parts = []
    if target.session.dice_roller == 'd20':
        for part in tmp:
            if part['type'] == 'span':
                parts.extend(format_d20_dice(part['text']))
            else:
                parts.append(part)
    elif target.session.dice_roller == 'eote':
        for part in tmp:
            if part['type'] == 'span':
                parts.extend(format_eote_dice(part['text']))
            else:
                parts.append(part)
    target.formatted = parts


def format_urls(message):
    """Formats any http/https URLs in the chat message.

    :params message: The message to process
    :type message: ``unicode``
    :return: The formatted message
    :rtype: ``list``
    """
    url_regexp = re.compile('http[^\s]*')
    parts = []
    while message:
        url_match = re.search(url_regexp, message)
        if url_match:
            if url_match.start() > 0:
                parts.append({'type': 'span',
                              'text': message[0:url_match.start()]})
            parts.append({'type': 'a',
                          'text': url_match.group(0),
                          'attrs': {'href': url_match.group(0),
                                    'target': '_blank'}})
            message = message[url_match.end():]
        else:
            parts.append({'type': 'span',
                          'text': message})
            message = ''
    return parts


def format_d20_dice(message):
    """Format the D20 dice for the ``message``

    :params message: The message to process
    :type message: ``unicode``
    :return: The formatted dice rolls
    :rtype: ``list``
    """
    parts = []
    while message:
        calc_match = re.search(calculation_regexp, message)
        if calc_match and calc_match.group(0).strip() != '':
            start = calc_match.start()
            if start > 0:
                parts.append({'type': 'span',
                              'text': message[0:start]})
            tokens = process_unary(add_dice(tokenise(calc_match.group(0))))
            total = calculate(infix_to_postfix(tokens))
            if calc_match.group(0).strip() == ' '.join([t[1] for t in tokens]).strip():
                parts.append({'type': 'span',
                              'text': calc_match.group(0)})
            else:
                if ' '.join([t[1] for t in tokens]).strip() == str(int(round(total))):
                    parts.append({'type': 'span',
                                  'text': '%s = %i' % (calc_match.group(0),
                                                       int(round(total)))})
                else:
                    parts.append({'type': 'span',
                                  'text': '%s = %s = %i' % (calc_match.group(0),
                                                            ' '.join([t[1] for t in tokens]),
                                                            int(round(total)))})
            message = message[calc_match.end():]
        else:
            parts.append({'type': 'span',
                          'text': message})
            message = ''
    return parts


def format_eote_dice(message):
    """Format the Edge-of-the-Empire dice rolls for the ``message``.

    :params message: The message to process
    :type message: ``unicode``
    :return: The formatted dice rolls
    :rtype: ``list``
    """
    parts = []
    eote_regexp = re.compile('([0-9]+[bapsdcf]\s*)+', re.IGNORECASE)
    dice_regexp = re.compile('([0-9]+[bapsdcf])', re.IGNORECASE)
    d100_regexp = re.compile('d100', re.IGNORECASE)
    while message:
        eote_match = re.search(eote_regexp, message)
        d100_match = re.search(d100_regexp, message)
        if (eote_match and not d100_match) or (eote_match and d100_match and eote_match.start() < d100_match.start()):
            if eote_match.start() > 0:
                parts.append({'type': 'span',
                              'text': message[0:eote_match.start()]})
            message = re.sub(eote_regexp, '%s', message, count=1)
            outcomes = {'success': 0, 'advantage': 0, 'triumph': 0,
                        'failure': 0, 'threat': 0, 'despair': 0,
                        'lightside': 0, 'darkside': 0}
            rolled_dice = []
            dice_results = []
            for dice in re.finditer(dice_regexp, eote_match.group(0)):
                count = int(dice.group(0)[:-1])
                die = dice.group(0)[-1]
                for _ in range(0, count):
                    if die.lower() == 'b':
                        rolled_dice.append({'type': 'span',
                                            'attrs': {'class': 'eote eote-boost',
                                                      'title': 'Boost Die'}})
                        value = random.randint(1, 6)
                        if value == 3:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-success',
                                                           'title': 'Success'}})
                            outcomes['success'] = outcomes['success'] + 1
                        elif value == 4:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-success-advantage',
                                                           'title': 'Success &amp; Advantage'}})
                            outcomes['success'] = outcomes['success'] + 1
                            outcomes['advantage'] = outcomes['advantage'] + 1
                        elif value == 5:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-advantage-double',
                                                           'title': 'Double Advantage'}})
                            outcomes['advantage'] = outcomes['advantage'] + 2
                        elif value == 6:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-advantage',
                                                           'title': 'Advantage'}})
                            outcomes['advantage'] = outcomes['advantage'] + 1
                    elif die.lower() == 'a':
                        rolled_dice.append({'type': 'span',
                                            'attrs': {'class': 'eote eote-ability',
                                                      'title': 'Ability Die'}})
                        value = random.randint(1, 8)
                        if 2 <= value <= 3:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-success',
                                                           'title': 'Success'}})
                            outcomes['success'] = outcomes['success'] + 1
                        elif value == 4:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-success-double',
                                                           'title': 'Double Success'}})
                            outcomes['success'] = outcomes['success'] + 2
                        elif 5 <= value <= 6:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-advantage',
                                                           'title': 'Advantage'}})
                            outcomes['advantage'] = outcomes['advantage'] + 1
                        elif value == 7:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-success-advantage',
                                                           'title': 'Success &amp; Advantage'}})
                            outcomes['success'] = outcomes['success'] + 1
                            outcomes['advantage'] = outcomes['advantage'] + 1
                        elif value == 8:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-advantage-double',
                                                           'title': 'Double Advantage'}})
                            outcomes['advantage'] = outcomes['advantage'] + 2
                    elif die.lower() == 'p':
                        rolled_dice.append({'type': 'span',
                                            'attrs': {'class': 'eote eote-proficiency',
                                                      'title': 'Proficiency Die'}})
                        value = random.randint(1, 12)
                        if 2 <= value <= 3:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-success',
                                                           'title': 'Success'}})
                            outcomes['success'] = outcomes['success'] + 1
                        elif 4 <= value <= 5:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-success-double',
                                                           'title': 'Double Success'}})
                            outcomes['success'] = outcomes['success'] + 2
                        elif value == 6:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-advantage',
                                                           'title': 'Advantage'}})
                            outcomes['advantage'] = outcomes['advantage'] + 1
                        elif 7 <= value <= 9:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-success-advantage',
                                                           'title': 'Success &amp; Advantage'}})
                            outcomes['success'] = outcomes['success'] + 1
                            outcomes['advantage'] = outcomes['advantage'] + 1
                        elif 10 <= value <= 11:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-advantage-double',
                                                           'title': 'Double Advantage'}})
                            outcomes['advantage'] = outcomes['advantage'] + 2
                        elif value == 12:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-triumph',
                                                           'title': 'Triumph'}})
                            outcomes['triumph'] = outcomes['triumph'] + 1
                            outcomes['success'] = outcomes['success'] + 1
                    elif die.lower() == 's':
                        rolled_dice.append({'type': 'span',
                                            'attrs': {'class': 'eote eote-setback',
                                                      'title': 'Setback Die'}})
                        value = random.randint(1, 6)
                        if 3 <= value <= 4:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-failure',
                                                           'title': 'Failure'}})
                            outcomes['failure'] = outcomes['failure'] + 1
                        elif 5 <= value <= 6:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-threat',
                                                           'title': 'Threat'}})
                            outcomes['threat'] = outcomes['threat'] + 1
                    elif die.lower() == 'd':
                        rolled_dice.append({'type': 'span',
                                            'attrs': {'class': 'eote eote-difficulty',
                                                      'title': 'Difficulty Die'}})
                        value = random.randint(1, 8)
                        if value == 2:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-failure',
                                                           'title': 'Failure'}})
                            outcomes['failure'] = outcomes['failure'] + 1
                        elif value == 3:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-failure-double',
                                                           'title': 'Double Failure'}})
                            outcomes['failure'] = outcomes['failure'] + 2
                        elif 4 <= value <= 6:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-threat',
                                                           'title': 'Threat'}})
                            outcomes['threat'] = outcomes['threat'] + 1
                        elif value == 7:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-threat-double',
                                                           'title': 'Double Threat'}})
                            outcomes['threat'] = outcomes['threat'] + 2
                        elif value == 8:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-failure-threat',
                                                           'title': 'Failure &amp; Threat'}})
                            outcomes['failure'] = outcomes['failure'] + 1
                            outcomes['threat'] = outcomes['threat'] + 1
                    elif die.lower() == 'c':
                        rolled_dice.append({'type': 'span',
                                            'attrs': {'class': 'eote eote-challenge',
                                                      'title': 'Challenge Die'}})
                        value = random.randint(1, 12)
                        if 2 <= value <= 3:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-failure',
                                                           'title': 'Failure'}})
                            outcomes['failure'] = outcomes['failure'] + 1
                        elif 4 <= value <= 5:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-failure-double',
                                                           'title': 'Double Failure'}})
                            outcomes['failure'] = outcomes['failure'] + 2
                        elif 6 <= value <= 7:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-threat',
                                                           'title': 'Threat'}})
                            outcomes['threat'] = outcomes['threat'] + 1
                        elif 8 <= value <= 9:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-failure-threat',
                                                           'title': 'Failure &amp; Threat'}})
                            outcomes['failure'] = outcomes['failure'] + 1
                            outcomes['threat'] = outcomes['threat'] + 1
                        elif 10 <= value <= 11:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-threat-double',
                                                           'title': 'Double Threat'}})
                            outcomes['threat'] = outcomes['threat'] + 2
                        elif value == 12:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-despair',
                                                           'title': 'Despair'}})
                            outcomes['failure'] = outcomes['failure'] + 1
                            outcomes['despair'] = outcomes['despair'] + 1
                    elif die.lower() == 'f':
                        rolled_dice.append({'type': 'span',
                                            'attrs': {'class': 'eote eote-force',
                                                      'title': 'Force Die'}})
                        value = random.randint(1, 12)
                        if 1 <= value <= 6:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-darkside',
                                                           'title': 'Darkside'}})
                            outcomes['darkside'] = outcomes['darkside'] + 1
                        elif value == 7:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-darkside-double',
                                                           'title': 'Double Darkside'}})
                            outcomes['darkside'] = outcomes['darkside'] + 2
                        elif 8 <= value <= 9:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-lightside',
                                                           'title': 'Lightside'}})
                            outcomes['lightside'] = outcomes['lightside'] + 1
                        elif 10 <= value <= 12:
                            dice_results.append({'type': 'span',
                                                 'attrs': {'class': 'eote eote-lightside-double',
                                                           'title': 'Double Lightside'}})
                            outcomes['lightside'] = outcomes['lightside'] + 2
            parts.extend(rolled_dice)
            parts.append({'type': 'span',
                          'text': ' = '})
            parts.extend(dice_results)
            parts.append({'type': 'span',
                          'text': ' = '})
            success = outcomes['success'] - outcomes['failure']
            if success > 0:
                parts.extend([{'type': 'span',
                               'attrs': {'class': 'eote eote-success',
                                         'title': 'Success'}} for _ in range(0, success)])
            elif success < 0:
                parts.extend([{'type': 'span',
                               'attrs': {'class': 'eote eote-failure',
                                         'title': 'Failure'}} for _ in range(0, abs(success))])
            advantage = outcomes['advantage'] - outcomes['threat']
            if advantage > 0:
                parts.extend([{'type': 'span',
                               'attrs': {'class': 'eote eote-advantage',
                                         'title': 'Advantage'}} for _ in range(0, advantage)])
            elif advantage < 0:
                parts.extend([{'type': 'span',
                               'attrs': {'class': 'eote eote-threat',
                                         'title': 'Threat'}} for _ in range(0, abs(success))])
            parts.extend([{'type': 'span',
                           'attrs': {'class': 'eote eote-triumph',
                                     'title': 'Triumph'}} for _ in range(0, outcomes['triumph'])])
            parts.extend([{'type': 'span',
                           'attrs': {'class': 'eote eote-despair',
                                     'title': 'Despair'}} for _ in range(0, outcomes['despair'])])
            parts.extend([{'type': 'span',
                           'attrs': {'class': 'eote eote-darkside',
                                     'title': 'Darkside'}} for _ in range(0, outcomes['darkside'])])
            parts.extend([{'type': 'span',
                           'attrs': {'class': 'eote eote-lightside',
                                     'title': 'Lightside'}} for _ in range(0, outcomes['lightside'])])
            message = message[eote_match.end():]
        elif (not eote_match and d100_match) or (eote_match and d100_match and d100_match.start() < eote_match.start()):
            if d100_match.start() > 0:
                parts.append({'type': 'span',
                              'text': message[0:d100_match.start()]})
            parts.append({'type': 'span',
                          'text': 'D100 = %i' % random.randint(1, 100)})
            message = message[d100_match.end():]
        else:
            parts.append({'type': 'span',
                          'text': message})
            message = ''
    return parts

register_component(ChatMessage, actions=['list', 'new', 'item'])
