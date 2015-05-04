# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""
import json

from formencode import validators, schema, foreach, Any, All, Invalid
from sqlalchemy import and_

from webrpg.components.rule_set import RULE_SETS
from webrpg.components.user import UserExistsValidator
from webrpg.components.util import (get_current_user, EmberSchema)
from webrpg.models import DBSession, Character

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
        query = query.filter(Character.user_id == request.params['user_id'])
    return query


class UpdateStatColumnSchema(EmberSchema):

    id = validators.UnicodeString(not_empty=True)
    value = validators.UnicodeString(if_empty=None)


class UpdateStatRowSchema(EmberSchema):

    columns = foreach.ForEach(UpdateStatColumnSchema())


class UpdateStatTableSchema(EmberSchema):

    rows = foreach.ForEach(UpdateStatRowSchema())


class UpdateCharacterSchema(EmberSchema):

    stats = foreach.ForEach(UpdateStatTableSchema())
    ruleSet = validators.UnicodeString()


def update_character_param_transform(params):
    rule_set = RULE_SETS[params['ruleSet']]
    rule_columns = []
    if 'stats' in rule_set:
        for stat_table in rule_set['stats']:
            if 'rows' in stat_table:
                for stat_row in stat_table['rows']:
                    if 'columns' in stat_row:
                        for stat_column in stat_row['columns']:
                            if stat_column['editable']:
                                rule_columns.append(('%s.%s' % (stat_table['id'], stat_column['id']), stat_column['data_type']))
    rule_columns = dict(rule_columns)
    new_params = {'attr': None}
    attr = {}
    if 'stats' in params:
        for stat_table in params['stats']:
            if 'rows' in stat_table:
                for stat_row in stat_table['rows']:
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
                                    attr[stat_column['id']] = stat_column['value']
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
                                   'param_transform': update_character_param_transform}
                        }}
