# -*- coding: utf-8 -*-
"""
################################################
Handles all character-related model interactions
################################################

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""
import json
import re

from copy import deepcopy
from formencode import validators, foreach
from pkg_resources import resource_string
from sqlalchemy import Column, Integer, Unicode, UnicodeText, ForeignKey
from sqlalchemy.orm import relationship

from webrpg.calculator import add_variables, infix_to_postfix, calculate, tokenise, process_unary
from webrpg.components import register_component
from webrpg.models import Base, JSONAPIMixin
from webrpg.util import (JSONAPISchema, DynamicSchema, DictValidator)

RULE_SETS = {}
RULE_SETS['dnd5e'] = json.loads(resource_string('webrpg', 'data/dnd5e.json').decode('utf8'))
RULE_SETS['dnd5em'] = json.loads(resource_string('webrpg', 'data/dnd5em.json').decode('utf8'))
RULE_SETS['eote'] = json.loads(resource_string('webrpg', 'data/eote.json').decode('utf8'))


class Character(Base, JSONAPIMixin):
    """The :class:`~webrpg.components.character.Character` represents a single character and its
    attributes, using a given rule-set. It has the following attributes: "attr", "rule_set",
    "game", "user"."""

    __tablename__ = 'characters'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', name='characters_user_id_fk'))
    game_id = Column(Integer, ForeignKey('games.id', name='characters_game_id_fk'))
    attr = Column(UnicodeText)
    rule_set = Column(Unicode(255))

    user = relationship('User')
    game = relationship('Game')

    __create_schema__ = JSONAPISchema('characters',
                                      attribute_schema=DynamicSchema({'rule_set': validators.OneOf(['dnd5e', 'dnd5em', 'eote'],
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
        """Computed attribute that extracts the correct title attribute for this
        :class:`~webrpg.components.character.Character`."""
        if self.attr:
            attrs = json.loads(self.attr)
            if 'title' in RULE_SETS[self.rule_set] and RULE_SETS[self.rule_set]['title'] in attrs:
                return attrs[RULE_SETS[self.rule_set]['title']]
        return 'Unnamed'

    @property
    def stats(self):
        """The stats property contains a ``list`` of ``dict`` that represent the
        attributes defined by the rule set and their values. Loads stored values
        from the "attr" attribute."""
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
                        # Calculate base attribute values
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
                                stat_column['action'] = {'title': source_column['title'] if 'title' in source_column else '',
                                                         'target': 'setChatMessage',
                                                         'content': ''}
                                if 'title' in source_column['action']:
                                    if multirow:
                                        stat_column['action']['title'] = ' '.join([t[1] for t in process_unary(add_variables(tokenise(source_column['action']['title'] % {'rowid': rowid}), attrs))])
                                    else:
                                        stat_column['action']['title'] = ' '.join([t[1] for t in process_unary(add_variables(tokenise(source_column['action']['title']), attrs))])
                                if 'target' in source_column['action']:
                                    stat_column['action']['target'] = source_column['action']['target']
                                if 'content' in source_column['action']:
                                    content = source_column['action']['content']
                                    if multirow:
                                        content = content % {'rowid': rowid}
                                    if 'calculate' in source_column['action'] and source_column['action']['calculate']:
                                        # If "calculate" is set, run full calculation
                                        calc_match = re.search(re.compile('\$([^$]*)\$'), content)
                                        while calc_match:
                                            if calc_match.group(0).strip() == '':
                                                break
                                            content = re.sub(re.compile('\$([^$]*)\$'),
                                                             str(calculate(infix_to_postfix(add_variables(tokenise(calc_match.group(1)), attrs)))),
                                                             content,
                                                             count=1)
                                            calc_match = re.search(re.compile('\$([^$]*)\$'), content)
                                        stat_row['action']['content'] = content
                                    else:
                                        # Otherwise just replace variables
                                        stat_column['action']['content'] = ' '.join([t[1] for t in process_unary(add_variables(tokenise(content), attrs))])
                        if 'action' in source_row:
                            # Calculate row-level actions
                            stat_row['action'] = {'title': source_row['title'] if 'title' in source_row else '',
                                                  'target': 'setChatMessage',
                                                  'content': ''}
                            if 'title' in source_row['action']:
                                stat_row['action']['title'] = ' '.join([t[1] for t in process_unary(add_variables(tokenise(source_row['action']['title']), attrs))])
                            if 'target' in source_row['action']:
                                stat_row['action']['target'] = source_row['action']['target']
                            if 'content' in source_row['action']:
                                content = source_row['action']['content']
                                if 'calculate' in source_row['action'] and source_row['action']['calculate']:
                                    # If "calculate" is set, run full calculation
                                    calc_match = re.search(re.compile('\$([^$]*)\$'), content)
                                    while calc_match:
                                        if calc_match.group(0).strip() == '':
                                            break
                                        content = re.sub(re.compile('\$([^$]*)\$'),
                                                         str(calculate(infix_to_postfix(add_variables(tokenise(calc_match.group(1)), attrs)))),
                                                         content,
                                                         count=1)
                                        calc_match = re.search(re.compile('\$([^$]*)\$'), content)
                                    stat_row['action']['content'] = content
                                else:
                                    # Otherwise just replace variables
                                    stat_row['action']['content'] = ' '.join([t[1] for t in process_unary(add_variables(tokenise(content), attrs))])
                        stat_table['rows'].append(stat_row)
                stats.append(stat_table)
        return stats

    @stats.setter
    def stats(self, data):
        """Updates the stored "attr" stats for this :class:`~webrpg.components.character.Character`."""
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
        if user and self.user_id == user.id:
            return True
        else:
            return self.game.has_role(user, 'owner')


register_component(Character, actions=['new', 'list', 'item', 'update', 'delete'])
