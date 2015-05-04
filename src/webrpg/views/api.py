# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""

import inflection
import json
import transaction

from formencode import Invalid, schema, validators, All
from pyramid.httpexceptions import (HTTPNotFound, HTTPMethodNotAllowed, HTTPClientError, HTTPUnauthorized)
from pyramid.view import view_config
from sqlalchemy import (and_)

from webrpg.models import (DBSession, User, Game, Session, ChatMessage)
from webrpg.components import (user, game, session, chat_message, character, rule_set)

def init(config):
    config.add_route('login', '/api/users/login')
    config.add_route('api.collection', '/api/{model}')
    config.add_route('api.item', '/api/{model}/{iid}')
    config.add_route('session.refresh', '/api/sessions/{iid}/refresh')


def raise_json_exception(base, body='{}'):
    if isinstance(body, dict):
        body = json.dumps(body)
    exception = base(headers=[('Content-Type', 'application/json; charset=utf8')],
                     body=body)
    raise exception


def invalid_to_error_dict(e):
    errors = {}
    if e.error_dict:
        for key, value in e.error_dict.items():
            if isinstance(value, Invalid) and value.error_dict:
                errors[key] = invalid_to_error_dict(value)
            else:
                errors[key] = str(value)
    else:
        errors['_'] = str(e)
    return errors


class State(object):
    
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class PasswordValidator(schema.FancyValidator):
    
    messages = {'nologin': 'No user exists with the given e-mail address or the password is incorrect'}
    
    def _convert_to_python(self, value, state):
        value['email'] = value['email'].lower()
        return value
    
    def _validate_python(self, value, state):
        user = state.dbsession.query(User).filter(User.email == value['email'].lower()).first()
        if user:
            if not user.password_matches(value['password']):
                raise Invalid(self.message('nologin', state), value, state)
        else:
            raise Invalid(self.message('nologin', state), value, state)


class LoginUserSchema(schema.Schema):

    email = validators.Email(not_empty=True)
    password = validators.UnicodeString(not_empty=True)

    chained_validators = [PasswordValidator()]


@view_config(route_name='login', renderer='json')
def login(request):
    dbsession = DBSession()
    try:
        params = LoginUserSchema().to_python(request.POST, State(dbsession=dbsession))
        user = dbsession.query(User).filter(User.email == params['email']).first()
        return {'user': user.as_dict()}
    except Invalid as e:
        raise_json_exception(HTTPClientError, body=invalid_to_error_dict(e))


class ModelWrapperSchema(schema.Schema):
    
    def __init__(self, model_name, model_schema):
        self.add_field(model_name, model_schema)

MODELS = {}
MODELS.update(user.MODELS)
MODELS.update(game.MODELS)
MODELS.update(session.MODELS)
MODELS.update(chat_message.MODELS)
MODELS.update(character.MODELS)
MODELS.update(rule_set.MODELS)


def get_current_user(request):
    if 'X-WebRPG-Authentication' in request.headers:
        auth = request.headers['X-WebRPG-Authentication'].split(':')
        if len(auth) == 2:
            dbsession = DBSession()
            return dbsession.query(User).filter(User.id == auth[0]).first()
        else:
            return None
    else:
        return None


def access_check(request, options):
    if 'authenticate' in options and options['authenticate']:
        if not get_current_user(request):
            raise_json_exception(HTTPUnauthorized)


def authorisation_check(request, params, options):
    if 'authorisation' in options:
        if not options['authorisation'](request, params):
            raise_json_exception(HTTPUnauthorized)


@view_config(route_name='api.collection', renderer='json')
def handle_collection(request):
    model_name = inflection.singularize(request.matchdict['model'])
    if model_name in MODELS:
        try:
            if request.method == 'GET' and 'list' in MODELS[model_name]:
                access_check(request, MODELS[model_name]['list'])
                authorisation_check(request, None, MODELS[model_name]['list'])
                if 'class' in MODELS[model_name]:
                    dbsession = DBSession()
                    query = dbsession.query(MODELS[model_name]['class'])
                    if 'filter' in MODELS[model_name]['list']:
                        query = MODELS[model_name]['list']['filter'](request, query)
                    return {request.matchdict['model']: [m.as_dict() for m in query]}
                elif 'function' in MODELS[model_name]['list']:
                    return {request.matchdict['model']: MODELS[model_name]['list']['function'](request)}
                else:
                    raise raise_json_exception(HTTPMethodNotAllowed)
            elif request.method == 'POST' and 'new' in MODELS[model_name]:
                access_check(request, MODELS[model_name]['new'])
                dbsession = DBSession()
                schema = ModelWrapperSchema(model_name, MODELS[model_name]['new']['schema']())
                params = schema.to_python(json.loads(request.body.decode('utf8')),
                                          state=State(dbsession=dbsession))[model_name]
                if 'param_transform' in MODELS[model_name]['new']:
                    params = MODELS[model_name]['new']['param_transform'](params)
                authorisation_check(request, params, MODELS[model_name]['new'])
                with transaction.manager:
                    model = MODELS[model_name]['class'](**params)
                    dbsession.add(model)
                dbsession.add(model)
                return {model_name: model.as_dict()}
            else:
                raise raise_json_exception(HTTPMethodNotAllowed)
        except Invalid as e:
            raise raise_json_exception(HTTPClientError, {'error': invalid_to_error_dict(e)})
    else:
        raise_json_exception(HTTPNotFound)


@view_config(route_name='api.item', renderer='json')
def handle_item(request):
    model_name = inflection.singularize(request.matchdict['model'])
    if model_name in MODELS:
        try:
            if request.method == 'GET' and 'item' in MODELS[model_name]:
                access_check(request, MODELS[model_name]['item'])
                authorisation_check(request, None, MODELS[model_name]['item'])
                if 'class' in MODELS[model_name]:
                    dbsession = DBSession()
                    model = dbsession.query(MODELS[model_name]['class']).\
                            filter(MODELS[model_name]['class'].id == request.matchdict['iid']).\
                            first()
                    if model:
                        return {model_name: model.as_dict()}
                    else:
                        raise_json_exception(HTTPNotFound)
                elif 'function' in MODELS[model_name]['item']:
                    return {model_name: MODELS[model_name]['item']['function'](request)}
                else:
                    raise raise_json_exception(HTTPMethodNotAllowed)
            elif request.method == 'PUT' and 'update' in MODELS[model_name]:
                access_check(request, MODELS[model_name]['update'])
                authorisation_check(request, None, MODELS[model_name]['update'])
                if 'class' in MODELS[model_name]:
                    dbsession = DBSession()
                    model = dbsession.query(MODELS[model_name]['class']).filter(MODELS[model_name]['class'].id == request.matchdict['iid']).first()
                    if model:
                        schema = ModelWrapperSchema(model_name, MODELS[model_name]['update']['schema']())
                        params = schema.to_python(json.loads(request.body.decode('utf8')),
                                                  state=State(dbsession=dbsession))[model_name]
                        if 'param_transform' in MODELS[model_name]['update']:
                            params = MODELS[model_name]['update']['param_transform'](params)
                        with transaction.manager:
                            dbsession.add(model)
                            for key, value in params.items():
                                setattr(model, key, value)
                        dbsession.add(model)
                        return {model_name: model.as_dict()}
                    else:
                        raise_json_exception(HTTPNotFound)
                else:
                    raise_json_exception(HTTPNotFound)
            else:
                raise raise_json_exception(HTTPMethodNotAllowed)
        except Invalid as e:
            raise raise_json_exception(HTTPClientError, {'error': invalid_to_error_dict(e)})
    else:
        raise_json_exception(HTTPNotFound)


@view_config(route_name='session.refresh', renderer='json')
def handle_session_refresh(request):
    data = {}
    for request_model_name, value in request.params.items():
        model_name = inflection.singularize(request_model_name)
        if model_name in MODELS and 'refresh' in MODELS[model_name] and 'func' in MODELS[model_name]['refresh']:
            data[request_model_name] = MODELS[model_name]['refresh']['func'](request, value)
    return data
