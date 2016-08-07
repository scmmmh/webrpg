# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""

import json
import transaction

from decorator import decorator
from formencode import Invalid, FancyValidator
from pyramid.httpexceptions import (HTTPNotFound, HTTPMethodNotAllowed, HTTPClientError, HTTPUnauthorized,
    HTTPNoContent)
from pyramid.request import Request
from pyramid.view import view_config

from webrpg.components import COMPONENTS
from webrpg.models import DBSession
from webrpg.util import invalid_to_error_list, raise_json_exception


def init(config):
    config.add_route('login', '/api/users/login')
    config.add_route('api.collection', '/api/{model}')
    config.add_route('api.item', '/api/{model}/{iid}')
    config.add_route('session.refresh', '/api/sessions/{iid}/refresh')


def json_defaults():
    def wrapper(f, *args, **kwargs):
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        if request:
            request.response.headers['Cache-Control'] = 'no-cache'
            request.response.headers['Content-Type'] = 'application/vnd.api+json'
        return f(*args, **kwargs)
    return decorator(wrapper)


def get_current_user():
    from webrpg.components.user import User
    def wrapper(f, *args, **kwargs):
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        if request:
            request.current_user = None
            if 'X-WebRPG-Authentication' in request.headers:
                auth = request.headers['X-WebRPG-Authentication'].split(':')
                if len(auth) == 2:
                    dbsession = DBSession()
                    if auth[0] and auth[0] != 'null':
                        user = dbsession.query(User).filter(User.id == auth[0]).first()
                        request.current_user = user
        return f(*args, **kwargs)
    return decorator(wrapper)


class JSONAPIValidator(FancyValidator):

    messages = {'notjson': 'The given request does not contain a JSON body',
                'notdict': 'The given JSON request is not an object',
                'nodata': 'The given JSON request does not contain a "data" key'}

    def _to_python(self, value, state):
        try:
            value = json.loads(value)
            if isinstance(value, dict):
                if 'data' in value:
                    return value['data']
                else:
                    raise Invalid(self.message('nodata', state), value, state)
            else:
                raise Invalid(self.message('notdict', state), value, state)
        except ValueError:
            raise Invalid(self.message('notjson', state), value, state)


def handle_list_model(request, model_name):
    dbsession = DBSession()
    cls = COMPONENTS[model_name]['class']
    query = dbsession.query(cls)
    for key, value in request.params.items():
        if hasattr(cls, key):
            query = query.filter(getattr(cls, key) == value)
    response = {'data': [],
                'included': []}
    for obj in query:
        if obj.allow(request.current_user, 'view'):
            data, included = obj.as_dict(request=request)
            response['data'].append(data)
            if included:
                response['included'].extend(included)
    if not response['included']:
        del response['included']
    return response


def handle_new_model(request, model_name):
    dbsession = DBSession()
    data = JSONAPIValidator(not_empty=True).to_python(request.body)
    item = COMPONENTS[model_name]['class'].from_dict(data, dbsession)
    if item:
        with transaction.manager:
            dbsession.add(item)
            dbsession.flush()
            item_data, item_included = item.as_dict(request=request)
            response = {'data': item_data}
            if item_included:
                response['included'] = item_included
        return response
    return {}


@view_config(route_name='api.collection', renderer='json')
@get_current_user()
@json_defaults()
def handle_collection(request):
    model_name = request.matchdict['model']
    if model_name in COMPONENTS:
        try:
            if request.method == 'GET' and 'list' in COMPONENTS[model_name]['actions']:
                return handle_list_model(request, model_name)
            elif request.method == 'POST' and 'new' in COMPONENTS[model_name]['actions']:
                return handle_new_model(request, model_name)
            else:
                raise raise_json_exception(HTTPMethodNotAllowed)
        except Invalid as e:
            raise_json_exception(HTTPClientError, body=invalid_to_error_list(e))
    else:
        raise_json_exception(HTTPNotFound)


def handle_single_model(request, model_name):
    dbsession = DBSession()
    item = dbsession.query(COMPONENTS[model_name]['class']).filter(COMPONENTS[model_name]['class'].id == request.matchdict['iid']).first()
    if item:
        item_data, item_included = item.as_dict(request=request)
        response = {'data': item_data}
        if item_included:
            response['included'] = item_included
        return response
    else:
        raise_json_exception(HTTPNotFound)


def update_single_model(request, model_name):
    dbsession = DBSession()
    data = JSONAPIValidator(not_empty=True).to_python(request.body)
    item = dbsession.query(COMPONENTS[model_name]['class']).filter(COMPONENTS[model_name]['class'].id == request.matchdict['iid']).first()
    if item:
        with transaction.manager:
            dbsession.add(item)
            item.update_from_dict(data, dbsession)
            dbsession.flush()
            item_data, item_included = item.as_dict(request=request)
            response = {'data': item_data}
            if item_included:
                response['included'] = item_included
        return response
    else:
        raise_json_exception(HTTPNotFound)


def delete_single_model(request, model_name):
    dbsession = DBSession()
    item = dbsession.query(COMPONENTS[model_name]['class']).filter(COMPONENTS[model_name]['class'].id == request.matchdict['iid']).first()
    if item:
        with transaction.manager:
            dbsession.delete(item)
        raise_json_exception(HTTPNoContent)
    else:
        raise_json_exception(HTTPNotFound)


@view_config(route_name='api.item', renderer='json')
@get_current_user()
@json_defaults()
def handle_item(request):
    model_name = request.matchdict['model']
    if model_name in COMPONENTS:
        if request.method == 'GET' and 'item' in COMPONENTS[model_name]['actions']:
            return handle_single_model(request, model_name)
        elif request.method == 'PATCH' and 'update' in COMPONENTS[model_name]['actions']:
            return update_single_model(request, model_name)
        elif request.method == 'DELETE' and 'update' in COMPONENTS[model_name]['actions']:
            return delete_single_model(request, model_name)
        else:
            raise raise_json_exception(HTTPMethodNotAllowed)
    else:
        raise_json_exception(HTTPNotFound)
