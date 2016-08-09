# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""
import json

from formencode import Schema, Invalid, FancyValidator
from formencode.validators import OneOf


class DoNotStore(object):
    pass


class State(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class DictValidator(FancyValidator):

    messages = {'not_dict': 'This is not a dictionary object'}

    def to_python(self, value, state):
        if isinstance(value, dict):
            return value
        else:
            raise Invalid(self.message("not_dict", state), value, state)


class ListValidator(FancyValidator):

    messages = {'not_list': 'This is not a list object'}

    def to_python(self, value, state):
        if isinstance(value, list):
            return value
        else:
            raise Invalid(self.message("not_list", state), value, state)


class EmberSchema(Schema):
    
    allow_extra_fields = True
    filter_extra_fields = True


class DynamicSchema(EmberSchema):

    def __init__(self, fields, *args, **kwargs):
        EmberSchema.__init__(self, *args, **kwargs)
        for key, value in fields.items():
            if isinstance(value, dict):
                self.add_field(key, DynamicSchema(value))
            else:
                self.add_field(key, value)


class JSONAPISchema(EmberSchema):

    def __init__(self, type_, attribute_schema=None, relationship_schema=None):
        self.add_field('type', OneOf([type_]))
        if attribute_schema:
            self.add_field('attributes', attribute_schema)
        if relationship_schema:
            self.add_field('relationships', relationship_schema)


def raise_json_exception(base, body=[]):
    if isinstance(body, list):
        body = json.dumps({'errors': body})
    exception = base(headers=[('Cache-Control', 'no-cache'),
                              ('Content-Type', 'application/vnd.api+json')],
                     body=body)
    raise exception


def invalid_to_error_list(e, errors=None):
    if errors is None:
        errors = []
    if e.error_dict:
        for key, value in e.error_dict.items():
            if isinstance(value, Invalid) and value.error_dict:
                invalid_to_error_list(value, errors=errors)
            else:
                errors.append({'title': str(value),
                               'source': key.replace('_', '-')})
    else:
        errors.append({'title': str(e)})
    return errors
