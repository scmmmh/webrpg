# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""

import json

from formencode import validators, schema, All, Invalid
from pkg_resources import resource_string
from sqlalchemy import and_

from webrpg.components.util import (EmberSchema)

RULE_SETS = {}
RULE_SETS['dnd5e'] = json.loads(resource_string('webrpg', 'data/dnd5e.json').decode('utf8'))
RULE_SETS['dnd5em'] = json.loads(resource_string('webrpg', 'data/dnd5em.json').decode('utf8'))
RULE_SETS['eote'] = json.loads(resource_string('webrpg', 'data/eote.json').decode('utf8'))
 
for rule_set in RULE_SETS.values():
    if 'character_sheet' in rule_set:
        for group in rule_set['character_sheet']:
            group['type'] = 'AttributeGroup'
            for attr in group['attributes']:
                attr['type'] = 'Attribute'
                attr['id'] = '%s::%s' % (group['id'], attr['id'])
                if 'modifier' in attr:
                    attr['modifier']['id'] = '%s::%s' % (group['id'], attr['modifier']['id'])
                    attr['modifier']['type'] = 'Modifier'


def rule_sets(request):
    return list(RULE_SETS.values())


def rule_set(request):
    if request.matchdict['iid'] in RULE_SETS:
        return RULE_SETS[request.matchdict['iid']]
    else:
        return {}


MODELS = {'ruleSet': {'list': {'authenticate': True,
                               'function': rule_sets},
                      'item': {'authenticate': True,
                               'function': rule_set}}}
