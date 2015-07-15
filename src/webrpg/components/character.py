# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""
import json

from copy import deepcopy
from formencode import validators, schema, foreach, Any, All, Invalid
from sqlalchemy import and_

from webrpg.components.rule_set import RULE_SETS
from webrpg.components.user import UserExistsValidator
from webrpg.components.util import (get_current_user, EmberSchema)
from webrpg.models import DBSession, Character, Game, GameRole

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


MODELS = {'character': {'class': Character,
                        'new': {'authenticate': True,
                                'schema': NewCharacterSchema,
                                'param_transform': new_character_param_transform},
                        'list': {'authenticate': True,
                                 'filter': filter_list_characters},
                        'update': {'authenticate': True,
                                   'schema': UpdateCharacterSchema,
                                   'param_transform': update_character_param_transform},
                        'delete': {'authenticate': True}
                        }}
