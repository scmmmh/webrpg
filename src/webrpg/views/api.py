"""
#########################################
:mod:`~webrpg.views.api` - JSON API views
#########################################

Views that implement the JSON API: http://jsonapi.org/.

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
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
    """Initialise the JSON API routes."""
    config.add_route('login', '/api/users/login')
    config.add_route('api.collection', '/api/{model}')
    config.add_route('api.item', '/api/{model}/{iid}')
    config.add_route('api.item.relationship', '/api/{model}/{iid}/{rid}')


def json_defaults():
    """Decorator that adds the headers the JSON API requires."""
    def wrapper(f, *args, **kwargs):
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        if request:
            request.response.headers['Cache-Control'] = 'no-cache'
            request.response.headers['Content-Type'] = 'application/vnd.api+json;charset=utf-8'
        return f(*args, **kwargs)
    return decorator(wrapper)


def get_current_user():
    """Decorator that sets the current :class:`~webrpg.components.user.User` into the current request."""
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
    """Formencode :class:`~formencode.FancyValidator` for validating the basic structure
    of a JSON API request."""

    messages = {'notjson': 'The given request does not contain a JSON body',
                'notdict': 'The given JSON request is not an object',
                'nodata': 'The given JSON request does not contain a "data" key'}

    def _to_python(self, value, state):
        try:
            value = json.loads(value.decode('utf-8'))
            if isinstance(value, dict):
                if 'data' in value:
                    return value['data']
                else:
                    raise Invalid(self.message('nodata', state), value, state)
            else:
                raise Invalid(self.message('notdict', state), value, state)
        except ValueError:
            raise Invalid(self.message('notjson', state), value, state)


def filter_list(items):
    """Filter duplicate entries in the ``items``. This is primarily used by the
    "included" response to ensure that each side-loaded data entry is included
    only once. Filters duplicates based on the "type" and "id" attributes."""
    seen = []
    result = []
    for item in items:
        uid = (item['type'], item['id'])
        if uid not in seen:
            result.append(item)
            seen.append(uid)
    return result


def handle_list_model(request, model_name):
    """Handler for "GET /model_name" requests. Filters the response based on any query
    parameters. By default filters on equality, but by prefixing the query parameter
    with "$gt:" can filter for values greater than the given value.

    Only includes data that the current user has the "view" permission for.

    :param request: The request to handle
    :type request: :class:`~pyramid.request.Request`
    :param model_name: The name of the model to load
    :type model_name: ``unicode``
    :return: The JSON API response
    :rtype: ``dict``
    """
    dbsession = DBSession()
    cls = COMPONENTS[model_name]['class']
    query = dbsession.query(cls)
    for key, value in request.params.items():
        comparator = 'eq'
        if key.startswith('$') and key.find(':') > 0:
            comparator = key[1:key.find(':')]
            key = key[key.find(':') + 1:]
        if hasattr(cls, key):
            if comparator == 'eq':
                query = query.filter(getattr(cls, key) == value)
            elif comparator == 'gt':
                query = query.filter(getattr(cls, key) > value)
    response = {'data': [],
                'included': []}
    query = query.order_by(cls.id)
    for obj in query:
        if obj.allow(request.current_user, 'view'):
            data, included = obj.as_dict(request=request)
            response['data'].append(data)
            if included:
                response['included'].extend(included)
    if response['included']:
        response['included'] = filter_list(response['included'])
    else:
        del response['included']
    return response


def handle_new_model(request, model_name):
    """Handler for "POST /model_name" requests, creates a new instance
    of the given model, if the submitted data validates.

    :param request: The request to handle
    :type request: :class:`~pyramid.request.Request`
    :param model_name: The name of the model to load
    :type model_name: ``unicode``
    :return: The JSON API response
    :rtype: ``dict``
    """
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
                response['included'] = filter_list(item_included)
        return response
    return {}


@view_config(route_name='api.collection', renderer='json')
@get_current_user()
@json_defaults()
def handle_collection(request):
    """Handles requests to the collection URL /model_name, dispatching to
    :func:`~webrpg.views.api.handle_list_model` or :func:`~webrpg.views.api.handle_new_model`
    depending on the request method.

    :param request: The request to handle
    :type request: :class:`~pyramid.request.Request`
    :return: The JSON API response
    :rtype: ``dict``
    """
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
    """Handles "GET /model_name/id" requests.

    :param request: The request to handle
    :type request: :class:`~pyramid.request.Request`
    :param model_name: The name of the model to load
    :type model_name: ``unicode``
    :return: The JSON API response
    :rtype: ``dict``
    """
    dbsession = DBSession()
    item = dbsession.query(COMPONENTS[model_name]['class']).filter(COMPONENTS[model_name]['class'].id == request.matchdict['iid']).first()
    if item:
        if item.allow(request.current_user, 'view'):
            item_data, item_included = item.as_dict(request=request)
            response = {'data': item_data}
            if item_included:
                response['included'] = filter_list(item_included)
            return response
        else:
            raise_json_exception(HTTPUnauthorized)
    else:
        raise_json_exception(HTTPNotFound)


def update_single_model(request, model_name):
    """Handles "PATCH /model_name/id" requests, updating the instance if
    the data validates.

    :param request: The request to handle
    :type request: :class:`~pyramid.request.Request`
    :param model_name: The name of the model to load
    :type model_name: ``unicode``
    :return: The JSON API response
    :rtype: ``dict``
    """
    dbsession = DBSession()
    data = JSONAPIValidator(not_empty=True).to_python(request.body)
    item = dbsession.query(COMPONENTS[model_name]['class']).filter(COMPONENTS[model_name]['class'].id == request.matchdict['iid']).first()
    if item:
        if item.allow(request.current_user, 'edit'):
            with transaction.manager:
                dbsession.add(item)
                item.update_from_dict(data, dbsession)
                dbsession.flush()
                item_data, item_included = item.as_dict(request=request)
                response = {'data': item_data}
                if item_included:
                    response['included'] = filter_list(item_included)
            return response
        else:
            raise_json_exception(HTTPUnauthorized)
    else:
        raise_json_exception(HTTPNotFound)


def delete_single_model(request, model_name):
    """Handles "DELETE /model_name/id" requests, deleting the instance if the
    user has the necessary permissions.

    :param request: The request to handle
    :type request: :class:`~pyramid.request.Request`
    :param model_name: The name of the model to load
    :type model_name: ``unicode``
    :return: The JSON API response
    :rtype: ``dict``
    """
    dbsession = DBSession()
    item = dbsession.query(COMPONENTS[model_name]['class']).filter(COMPONENTS[model_name]['class'].id == request.matchdict['iid']).first()
    if item:
        if item.allow(request.current_user, 'delete'):
            with transaction.manager:
                dbsession.delete(item)
            raise_json_exception(HTTPNoContent)
        else:
            raise_json_exception(HTTPUnauthorized)
    else:
        raise_json_exception(HTTPNotFound)


@view_config(route_name='api.item', renderer='json')
@get_current_user()
@json_defaults()
def handle_item(request):
    """Handles "/model_name/id" requests, dispatching to :func:`~webrpg.api.handle_single_model`,
    :func:`~webrpg.api.update_single_model`, or :func:`~webrpg.api.delete_single_model` functions
    depending on the request method.

    :param request: The request to handle
    :type request: :class:`~pyramid.request.Request`
    :return: The JSON API response
    :rtype: ``dict``
    """
    model_name = request.matchdict['model']
    if model_name in COMPONENTS:
        if request.method == 'GET' and 'item' in COMPONENTS[model_name]['actions']:
            return handle_single_model(request, model_name)
        elif request.method == 'PATCH' and 'update' in COMPONENTS[model_name]['actions']:
            return update_single_model(request, model_name)
        elif request.method == 'DELETE' and 'delete' in COMPONENTS[model_name]['actions']:
            return delete_single_model(request, model_name)
        else:
            raise raise_json_exception(HTTPMethodNotAllowed)
    else:
        raise_json_exception(HTTPNotFound)


def handle_fetch_relationship(request, model_name):
    """Handles "GET /model_name/id/relationship" requests, returning all models for the given
    relationship for the model item, if the user has permission to view the item.

    :param request: The request to handle
    :type request: :class:`~pyramid.request.Request`
    :param model_name: The name of the model to load
    :type model_name: ``unicode``
    :return: The JSON API response
    :rtype: ``dict``
    """
    dbsession = DBSession()
    item = dbsession.query(COMPONENTS[model_name]['class']).filter(COMPONENTS[model_name]['class'].id == request.matchdict['iid']).first()
    if item:
        if item.allow(request.current_user, 'view'):
            rel_name = request.matchdict['rid']
            if hasattr(item, '__json_relationships__') and rel_name in item.__json_relationships__:
                try:
                    response = {'data': [],
                                'included': []}
                    for rel in getattr(item, rel_name):
                        if rel and rel.allow(request.current_user, 'view'):
                            rel_data, rel_included = rel.as_dict(request=request)
                            response['data'].append(rel_data)
                            response['included'].extend(rel_included)
                except:
                    rel = getattr(item, rel_name)
                    if rel and rel.allow(request.current_user, 'view'):
                        rel_data, rel_included = rel.as_dict(request=request)
                        response = {'data': rel_data,
                                    'included': rel_included}
                    else:
                        response = {'data': {},
                                    'included': []}
                if response['included']:
                    response['included'] = filter_list(response['included'])
                else:
                    del response['included']
                return response
            else:
                raise_json_exception(HTTPUnauthorized)
        else:
            raise_json_exception(HTTPNotFound)
    else:
        raise_json_exception(HTTPNotFound)


@view_config(route_name='api.item.relationship', renderer='json')
@get_current_user()
@json_defaults()
def handle_relationship(request):
    """Handles "/model_name/id/relationship" requests, dispatching to :func:`~webrpg.api.handle_fetch_relationship`
    depending on the request method.

    :param request: The request to handle
    :type request: :class:`~pyramid.request.Request`
    :return: The JSON API response
    :rtype: ``dict``
    """
    model_name = request.matchdict['model']
    if model_name in COMPONENTS:
        if request.method == 'GET':
            return handle_fetch_relationship(request, model_name)
        else:
            raise raise_json_exception(HTTPMethodNotAllowed)
    else:
        raise_json_exception(HTTPNotFound)
