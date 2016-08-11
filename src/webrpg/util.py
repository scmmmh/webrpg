"""
#######################################
:mod:`~webrpg.util` - Utility functions
#######################################

Generic utility functions and classes.

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
import json

from formencode import Schema, Invalid, FancyValidator
from formencode.validators import OneOf


class DoNotStore(object):
    """The :class:`~webrpg.util.DoNotStore` is used with formencode validation
    to indicate that a missing value is to be ignored."""
    pass


class State(object):
    """The :class:`~webrpg.util.State` is used to create an object with properties
    defined by the keyword arguments passed to the constructor."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class DictValidator(FancyValidator):
    """Formencode :class:`~formencode.FancyValidator` that checks that the given
    value is a ``dict`` object."""

    messages = {'not_dict': 'This is not a dictionary object'}

    def to_python(self, value, state):
        if isinstance(value, dict):
            return value
        else:
            raise Invalid(self.message("not_dict", state), value, state)


class ListValidator(FancyValidator):
    """Formencode :class:`~formencode.FancyValidator` that checks that the given
    value is a ``list`` object."""

    messages = {'not_list': 'This is not a list object'}

    def to_python(self, value, state):
        if isinstance(value, list):
            return value
        else:
            raise Invalid(self.message("not_list", state), value, state)


class BaseSchema(Schema):
    """Generic base :class:`~formencode.Schema` that ignores and filters any extra fields
    passed into the validation process."""

    allow_extra_fields = True
    filter_extra_fields = True


class DynamicSchema(BaseSchema):
    """The :class:`~webrpg.util.DynamicSchema` is a dynamic :class:`~formencode.Schema` that
    allows building a nested schema via a set of nested ``dict``."""

    def __init__(self, fields, *args, **kwargs):
        BaseSchema.__init__(self, *args, **kwargs)
        for key, value in fields.items():
            if isinstance(value, dict):
                self.add_field(key, DynamicSchema(value))
            else:
                self.add_field(key, value)


class JSONAPISchema(BaseSchema):
    """The :class:`~webrpg.util.JSONAPISchema` forms the basis for validating requests that
    follow the JSON API structure."""

    def __init__(self, type_, attribute_schema=None, relationship_schema=None):
        self.add_field('type', OneOf([type_]))
        if attribute_schema:
            self.add_field('attributes', attribute_schema)
        if relationship_schema:
            self.add_field('relationships', relationship_schema)


def raise_json_exception(base, body=[]):
    """Raise an exception, setting the necessary headers to make them work in a JSON API structure."""
    if isinstance(body, list):
        body = json.dumps({'errors': body})
    exception = base(headers=[('Cache-Control', 'no-cache'),
                              ('Content-Type', 'application/vnd.api+json')],
                     body=body)
    raise exception


def invalid_to_error_list(e, errors=None):
    """Converts a :class:`~formencode.Invalid` error into a list of errors structured according to
    the JSON API specification."""
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
