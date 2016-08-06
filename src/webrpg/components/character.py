# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""
import json
import re

from copy import deepcopy
from formencode import validators, schema, foreach, Any, All, Invalid
from sqlalchemy import and_, Column, Integer, Unicode, UnicodeText, ForeignKey
from sqlalchemy.orm import relationship

from webrpg.calculator import add_variables, infix_to_postfix, calculate, tokenise, process_unary
from webrpg.components import register_component
from webrpg.components.rule_set import RULE_SETS
from webrpg.components.game import Game, GameRole
from webrpg.models import DBSession, Base, JSONAPIMixin
from webrpg.util import (EmberSchema, JSONAPISchema, DynamicSchema)


class NewCharacterSchema(EmberSchema):
    
    user = validators.Number(not_empty=True)
    game = validators.Number(not_empty=True)
    ruleSet = validators.UnicodeString(not_empty=True)


def new_character_param_transform(params):
    return {'user_id': params['user'],
            'game_id': params['game'],
            'rule_set': params['ruleSet']}


def filter_list_characters(request, query):
    if 'game_id' in request.params:
        query = query.filter(Character.game_id == request.params['game_id'])
        if 'user_id' in request.params:
            dbsession = DBSession()
            game = dbsession.query(Game).join(Game.roles).filter(and_(Game.id == request.params['game_id'],
                                                                      GameRole.role == 'owner',
                                                                      GameRole.user_id == request.params['user_id'])).first()
            if game is None:
                query = query.filter(Character.user_id == request.params['user_id'])
    else:
        if 'user_id' in request.params:
            query = query.filter(Character.user_id == request.params['user_id'])
    return query


class UpdateStatColumnSchema(EmberSchema):

    id = validators.UnicodeString(not_empty=True)
    value = validators.UnicodeString(if_empty=None)


class UpdateStatRowSchema(EmberSchema):

    id = validators.UnicodeString(not_empty=True)
    columns = foreach.ForEach(UpdateStatColumnSchema())


class UpdateStatTableSchema(EmberSchema):

    id = validators.UnicodeString(not_empty=True)
    rows = foreach.ForEach(UpdateStatRowSchema())


class UpdateCharacterSchema(EmberSchema):

    stats = foreach.ForEach(UpdateStatTableSchema())
    ruleSet = validators.UnicodeString()


def update_character_param_transform(character, params):
    attrs = json.loads(character.attr) if character.attr else {}
    rule_set = RULE_SETS[params['ruleSet']]
    rule_columns = []
    multirows = []
    if 'stats' in rule_set:
        for stat_table in rule_set['stats']:
            if 'rows' in stat_table:
                for stat_row in stat_table['rows']:
                    if 'multirow' in stat_row and stat_row['multirow']:
                        if '%s.%s._ids' % (stat_table['id'], stat_row['id']) in attrs:
                            multirow_ids = attrs['%s.%s._ids' % (stat_table['id'], stat_row['id'])]
                            multirow_ids.append(max(multirow_ids) + 1)
                        else:
                            multirow_ids = [0]
                    else:
                        multirow_ids = [None]
                    for multirow_id in multirow_ids:
                        if multirow_id is not None:
                            multirows.append((('%s.%s._row' % (stat_table['id'], stat_row['id'])) % (multirow_id), []))
                        if 'columns' in stat_row:
                            for stat_column in stat_row['columns']:
                                if stat_column['editable']:
                                    if 'multirow' in stat_row and stat_row['multirow']:
                                        column_id = stat_column['id'] % (multirow_id,)
                                    else:
                                        column_id = stat_column['id']
                                    rule_columns.append(('%s.%s' % (stat_table['id'], column_id), stat_column['data_type']))
    rule_columns = dict(rule_columns)
    multirows = dict(multirows)
    new_params = {'attr': None}
    attr = {}
    if 'stats' in params:
        for stat_table in params['stats']:
            if 'rows' in stat_table:
                for stat_row in stat_table['rows']:
                    stat_row['id'] = stat_row['id'][stat_row['id'].find('.') + 1:]
                    if stat_row['id'] in multirows:
                        used_multirow = False
                    if 'columns' in stat_row:
                        for stat_column in stat_row['columns']:
                            if 'id' in stat_column and 'value' in stat_column:
                                stat_column['id'] = stat_column['id'][stat_column['id'].find('.') + 1:]
                                if stat_column['id'] in rule_columns:
                                    if rule_columns[stat_column['id']] == 'boolean':
                                        if stat_column['value'] and stat_column['value'].lower() == 'true':
                                            stat_column['value'] = True
                                        else:
                                            stat_column['value'] = False
                                    elif rule_columns[stat_column['id']] == 'number':
                                        try:
                                            stat_column['value'] = int(stat_column['value'])
                                        except:
                                            try:
                                                stat_column['value'] = float(stat_column['value'])
                                            except:
                                                stat_column['value'] = ''
                                    if stat_row['id'] in multirows and stat_column['value']:
                                        used_multirow = True
                                    attr[stat_column['id']] = stat_column['value']
                    if stat_row['id'] in multirows and used_multirow:
                        row_id = stat_row['id']
                        row_id = row_id[:row_id.rfind('.')]
                        multirow_id = int(row_id[row_id.rfind('.') + 1:])
                        row_id = '%s.%%i._ids' % (row_id[:row_id.rfind('.')])
                        if row_id in attr:
                            attr[row_id].append(multirow_id)
                        else:
                            attr[row_id] = [multirow_id]
    if attr:
        new_params['attr'] = json.dumps(attr)
    return new_params


#MODELS = {'character': {'class': Character,
#                        'new': {'authenticate': True,
#                                'schema': NewCharacterSchema,
#                                'param_transform': new_character_param_transform},
#                        'list': {'authenticate': True,
#                                 'filter': filter_list_characters},
#                        'update': {'authenticate': True,
#                                   'schema': UpdateCharacterSchema,
#                                   'param_transform': update_character_param_transform},
#                        'delete': {'authenticate': True}
#                        }}


class Character(Base, JSONAPIMixin):

    __tablename__ = 'characters'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', name='characters_user_id_fk'))
    game_id = Column(Integer, ForeignKey('games.id', name='characters_game_id_fk'))
    attr = Column(UnicodeText)
    rule_set = Column(Unicode(255))

    user = relationship('User')
    game = relationship('Game')

    __create_schema__ = JSONAPISchema('characters',
                                      attribute_schema=DynamicSchema({'rule_set': validators.OneOf(['dnd', 'eote'],
                                                                                                   not_empty=True)}),
                                      relationship_schema=DynamicSchema({'game': {'data': {'type': validators.OneOf(['games'],
                                                                                                                    not_empty=True),
                                                                                           'id': validators.Number}},
                                                                         'user': {'data': {'type': validators.OneOf(['users'],
                                                                                                                    not_empty=True),
                                                                                           'id': validators.Number}}}))

    __json_attributes__ = ['rule_set', 'stats']
    __json_relationships__ = ['user', 'game']

    @property
    def stats(self):
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
        return stats

    def allow(self, user, action):
        return True

    def as_old_dict(self):
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


register_component('characters', Character, actions=['new', 'item', 'update'])
