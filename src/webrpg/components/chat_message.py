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
from webrpg.models import Base, JSONAPIMixin
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

    __json_attributes__ = ['message']
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


@event.listens_for(ChatMessage.message, 'set', retval=True)
def calculate_dicerolls(target, value, old_value, initiator):
    """Event listener that automatically handles the dice rolls."""
    message = value
    substitutions = []
    if target.session.dice_roller == 'd20':
        calc_match = re.search(calculation_regexp, message)
        while calc_match:
            if calc_match.group(0).strip() == '':
                break
            tokens = process_unary(add_dice(tokenise(calc_match.group(0))))
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
    elif target.session.dice_roller == 'eote':
        eote_regexp = re.compile('([0-9]+[bapsdcf]\s*)+', re.IGNORECASE)
        dice_regexp = re.compile('([0-9]+[bapsdcf])', re.IGNORECASE)
        eote_match = re.search(eote_regexp, message)
        while eote_match:
            message = re.sub(eote_regexp, '%s', message, count=1)
            outcomes = {'success': 0, 'advantage': 0, 'triumph': 0,
                        'failure': 0, 'threat': 0, 'despair': 0,
                        'lightside': 0, 'darkside': 0}
            dice_list = []
            rolls = []
            for dice in re.finditer(dice_regexp, eote_match.group(0)):
                count = int(dice.group(0)[:-1])
                die = dice.group(0)[-1]
                for _ in range(0, count):
                    if die.lower() == 'b':
                        dice_list.append('<span class="eote eote-boost" title="Boost Die"></span>')
                        value = random.randint(1, 6)
                        if value == 3:
                            rolls.append('<span class="eote eote-success" title="Success"></span>')
                            outcomes['success'] = outcomes['success'] + 1
                        elif value == 4:
                            rolls.append('<span class="eote eote-success-advantage" title="Success &amp; Advantage"></span>')
                            outcomes['success'] = outcomes['success'] + 1
                            outcomes['advantage'] = outcomes['advantage'] + 1
                        elif value == 5:
                            rolls.append('<span class="eote eote-advantage-double" title="Double Advantage"></span>')
                            outcomes['advantage'] = outcomes['advantage'] + 2
                        elif value == 6:
                            rolls.append('<span class="eote eote-advantage" title="Advantage"></span>')
                            outcomes['advantage'] = outcomes['advantage'] + 1
                    elif die.lower() == 'a':
                        dice_list.append('<span class="eote eote-ability" title="Ability Die"></span>')
                        value = random.randint(1, 8)
                        if 2 <= value <= 3:
                            rolls.append('<span class="eote eote-success" title="Success"></span>')
                            outcomes['success'] = outcomes['success'] + 1
                        elif value == 4:
                            rolls.append('<span class="eote eote-success-double" title="Double Success"></span>')
                            outcomes['success'] = outcomes['success'] + 2
                        elif 5 <= value <= 6:
                            rolls.append('<span class="eote eote-advantage" title="Advantage"></span>')
                            outcomes['advantage'] = outcomes['advantage'] + 1
                        elif value == 7:
                            rolls.append('<span class="eote eote-success-advantage" title="Success &amp; Advantage"></span>')
                            outcomes['success'] = outcomes['success'] + 1
                            outcomes['advantage'] = outcomes['advantage'] + 1
                        elif value == 8:
                            rolls.append('<span class="eote eote-advantage-double" title="Double Advantage"></span>')
                            outcomes['advantage'] = outcomes['advantage'] + 2
                    elif die.lower() == 'p':
                        dice_list.append('<span class="eote eote-proficiency" title="Proficiency Die"></span>')
                        value = random.randint(1, 12)
                        if 2 <= value <= 3:
                            rolls.append('<span class="eote eote-success" title="Success"></span>')
                            outcomes['success'] = outcomes['success'] + 1
                        elif 4 <= value <= 5:
                            rolls.append('<span class="eote eote-success-double" title="Double Success"></span>')
                            outcomes['success'] = outcomes['success'] + 2
                        elif value == 6:
                            rolls.append('<span class="eote eote-advantage" title="Advantage"></span>')
                            outcomes['advantage'] = outcomes['advantage'] + 1
                        elif 7 <= value <= 9:
                            rolls.append('<span class="eote eote-success-advantage" title="Success &amp; Advantage"></span>')
                            outcomes['success'] = outcomes['success'] + 1
                            outcomes['advantage'] = outcomes['advantage'] + 1
                        elif 10 <= value <= 11:
                            rolls.append('<span class="eote eote-advantage-double" title="Double Advantage"></span>')
                            outcomes['advantage'] = outcomes['advantage'] + 2
                        elif value == 12:
                            rolls.append('<span class="eote eote-triumph" title="Triumph"></span>')
                            outcomes['triumph'] = outcomes['triumph'] + 1
                            outcomes['success'] = outcomes['success'] + 1
                    elif die.lower() == 's':
                        dice_list.append('<span class="eote eote-setback" title="Setback Die"></span>')
                        value = random.randint(1, 6)
                        if 3 <= value <= 4:
                            rolls.append('<span class="eote eote-failure" title="Failure"></span>')
                            outcomes['failure'] = outcomes['failure'] + 1
                        elif 5 <= value <= 6:
                            rolls.append('<span class="eote eote-threat" title="Threat"></span>')
                            outcomes['threat'] = outcomes['threat'] + 1
                    elif die.lower() == 'd':
                        dice_list.append('<span class="eote eote-difficulty" title="Difficulty Die"></span>')
                        value = random.randint(1, 8)
                        if value == 2:
                            rolls.append('<span class="eote eote-failure" title="Failure"></span>')
                            outcomes['failure'] = outcomes['failure'] + 1
                        elif value == 3:
                            rolls.append('<span class="eote eote-failure-double" title="Double Failure"></span>')
                            outcomes['failure'] = outcomes['failure'] + 2
                        elif 4 <= value <= 6:
                            rolls.append('<span class="eote eote-threat" title="Threat"></span>')
                            outcomes['threat'] = outcomes['threat'] + 1
                        elif value == 7:
                            rolls.append('<span class="eote eote-threat-double" title="Double Threat"></span>')
                            outcomes['threat'] = outcomes['threat'] + 2
                        elif value == 8:
                            rolls.append('<span class="eote eote-failure-threat" title="Failure &amp; Threat"></span>')
                            outcomes['failure'] = outcomes['failure'] + 1
                            outcomes['threat'] = outcomes['threat'] + 1
                    elif die.lower() == 'c':
                        dice_list.append('<span class="eote eote-challenge" title="Challenge Die"></span>')
                        value = random.randint(1, 12)
                        if 2 <= value <= 3:
                            rolls.append('<span class="eote eote-failure" title="Failure"></span>')
                            outcomes['failure'] = outcomes['failure'] + 1
                        elif 4 <= value <= 5:
                            rolls.append('<span class="eote eote-failure-double" title="Double Failure"></span>')
                            outcomes['failure'] = outcomes['failure'] + 2
                        elif 6 <= value <= 7:
                            rolls.append('<span class="eote eote-threat" title="Threat"></span>')
                            outcomes['threat'] = outcomes['threat'] + 1
                        elif 8 <= value <= 9:
                            rolls.append('<span class="eote eote-failure-threat" title="Failure &amp; Threat"></span>')
                            outcomes['failure'] = outcomes['failure'] + 1
                            outcomes['threat'] = outcomes['threat'] + 1
                        elif 10 <= value <= 11:
                            rolls.append('<span class="eote eote-threat-double" title="Double Threat"></span>')
                            outcomes['threat'] = outcomes['threat'] + 2
                        elif value == 12:
                            rolls.append('<span class="eote eote-despair" title="Despair"></span>')
                            outcomes['failure'] = outcomes['failure'] + 1
                            outcomes['despair'] = outcomes['despair'] + 1
                    elif die.lower() == 'f':
                        dice_list.append('<span class="eote eote-force" title="Force Die"></span>')
                        value = random.randint(1, 12)
                        if 1 <= value <= 6:
                            rolls.append('<span class="eote eote-darkside" title="Darkside"></span>')
                            outcomes['darkside'] = outcomes['darkside'] + 1
                        elif value == 7:
                            rolls.append('<span class="eote eote-darkside-double" title="Double Darkside"></span>')
                            outcomes['darkside'] = outcomes['darkside'] + 2
                        elif 8 <= value <= 9:
                            rolls.append('<span class="eote eote-lightside" title="Lightside"></span>')
                            outcomes['lightside'] = outcomes['lightside'] + 1
                        elif 10 <= value <= 12:
                            rolls.append('<span class="eote eote-lightside-double" title="Double Lightside"></span>')
                            outcomes['lightside'] = outcomes['lightside'] + 2
                success = outcomes['success'] - outcomes['failure']
                result = []
                if success > 0:
                    result.append('<span class="eote eote-success" title="Success"></span>' * success)
                elif success < 0:
                    result.append('<span class="eote eote-failure" title="Failure"></span>' * abs(success))
                advantage = outcomes['advantage'] - outcomes['threat']
                if advantage > 0:
                    result.append('<span class="eote eote-advantage" title="Advantage"></span>' * advantage)
                elif advantage < 0:
                    result.append('<span class="eote eote-threat" title="Threat"></span>' * abs(advantage))
                result.append('<span class="eote eote-triumph" title="Triumph"></span>' * outcomes['triumph'])
                result.append('<span class="eote eote-despair" title="Despair"></span>' * outcomes['despair'])
                result.append('<span class="eote eote-darkside" title="Darkside"></span>' * outcomes['darkside'])
                result.append('<span class="eote eote-lightside" title="Lightside"></span>' * outcomes['lightside'])
            substitutions.append('%s = %s = %s' % (' '.join(dice_list), ' '.join(rolls), ''.join(result)))
            eote_match = re.search(eote_regexp, message)
        while 'd100' in message:
            message = message.replace('d100', '%s', 1)
            substitutions.append('d100 = %i' % random.randint(1, 100))
    return message % tuple(substitutions)

register_component(ChatMessage, actions=['list', 'new', 'item'])
