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
from webrpg.util import (EmberSchema, JSONAPISchema, DynamicSchema, DictValidator)


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
                                      attribute_schema=DynamicSchema({'rule_set': validators.OneOf(['dnd5e', 'eote'],
                                                                                                   not_empty=True)}),
                                      relationship_schema=DynamicSchema({'game': {'data': {'type': validators.OneOf(['games'],
                                                                                                                    not_empty=True),
                                                                                           'id': validators.Number}},
                                                                         'user': {'data': {'type': validators.OneOf(['users'],
                                                                                                                    not_empty=True),
                                                                                           'id': validators.Number}}}))
    __update_schema__ = JSONAPISchema('characters',
                                      attribute_schema=DynamicSchema({'stats': foreach.ForEach(DictValidator())}))

    __json_attributes__ = ['rule_set', 'stats']
    __json_relationships__ = ['user', 'game']
    __json_computed__ = ['title']

    def title(self, request):
        if self.attr:
            attrs = json.loads(self.attr)
            if 'title' in RULE_SETS[self.rule_set] and RULE_SETS[self.rule_set]['title'] in attrs:
                return attrs[RULE_SETS[self.rule_set]['title']]
        return 'Unnamed'

    @property
    def stats(self):
        attrs = json.loads(self.attr) if self.attr else {}
        rule_set = deepcopy(RULE_SETS[self.rule_set]) if self.rule_set else {}
        stats = []
        if 'stats' in rule_set:
            for source_table in rule_set['stats']:
                table_id = source_table['id']
                stat_table = {'id': table_id,
                              'title': source_table['title'],
                              'rows': []}
                if 'columns' in source_table:
                    stat_table['columns'] = deepcopy(source_table['columns'])
                for source_row in source_table['rows']:
                    multirow = 'multirow' in source_row and source_row['multirow']
                    if multirow:
                        if '%s.__rowids' % table_id in attrs:
                            rowids = attrs['%s.__rowids' % table_id]
                            rowids.append(max(rowids) + 1)
                        else:
                            rowids = [0]
                    else:
                        rowids = [None]
                    for rowid in rowids:
                        stat_row = {'columns': []}
                        if 'title' in source_row:
                            stat_row['title'] = source_row['title']
                        if multirow:
                            stat_row['multirow'] = rowid
                        for source_column in source_row['columns']:
                            column_id = '%s.%s' % (source_table['id'], source_column['id'])
                            if multirow:
                                column_id = column_id % rowid
                            stat_column = {'id': column_id,
                                           'data_type': source_column['data_type'],
                                           'editable': source_column['editable']}
                            if 'options' in source_column:
                                stat_column['options'] = source_column['options']
                            if 'formula' in source_column:
                                # Handle calculated fields
                                if multirow:
                                    formula = source_column['formula'] % {'rowid': rowid}
                                else:
                                    formula = source_column['formula']
                                tokens = add_variables(tokenise(formula), attrs)
                                total = calculate(infix_to_postfix(tokens))
                                stat_column['value'] = total
                                attrs[column_id] = total
                            else:
                                if column_id in attrs:
                                    stat_column['value'] = attrs[column_id]
                                else:
                                    stat_column['value'] = ''
                            stat_row['columns'].append(stat_column)
                        for source_column, stat_column in zip(source_row['columns'], stat_row['columns']):
                            # Calculate column-level actions
                            if 'action' in source_column:
                                if 'action_title' in source_column:
                                    action_title = source_column['action_title']
                                else:
                                    action_title = source_column['title']
                                if multirow:
                                    action_title = action_title % {'rowid': rowid}
                                    action = source_column['action'] % {'rowid': rowid}
                                else:
                                    action = source_column['action']
                                stat_column['action'] = ' '.join([t[1] for t in process_unary(add_variables(tokenise(action), attrs))])
                                stat_column['action_title'] = ' '.join([t[1] for t in process_unary(add_variables(tokenise(action_title), attrs))])
                        if 'action' in source_row:
                            # Calculate row-level actions
                            if 'action_title' in source_row:
                                stat_row['action_title'] = source_row['action_title']
                            else:
                                stat_row['action_title'] = source_row['title']
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
                        stat_table['rows'].append(stat_row)
                stats.append(stat_table)
        return stats

    @stats.setter
    def stats(self, data):
        attrs = {}
        for table in data:
            rowids = []
            for row in table['rows']:
                multirow = 'multirow' in row
                has_value = False
                for column in row['columns']:
                    if 'editable' in column and column['editable']:
                        if 'value' in column:
                            if column['value']:
                                attrs[column['id']] = column['value']
                                has_value = True
                if multirow and has_value:
                    rowids.append(row['multirow'])
            if rowids:
                attrs['%s.__rowids' % table['id']] = rowids
        self.attr = json.dumps(attrs)

    def allow(self, user, action):
        return True


register_component('characters', Character, actions=['new', 'item', 'update'])
