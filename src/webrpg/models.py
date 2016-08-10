import inflection

from formencode import Invalid
from sqlalchemy.ext.declarative import (declarative_base)
from sqlalchemy.orm import (scoped_session, sessionmaker)
from zope.sqlalchemy import ZopeTransactionExtension

from webrpg.components import COMPONENTS
from webrpg.util import State, DoNotStore

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


def convert_keys(data):
    if isinstance(data, dict):
        return dict([(k.replace('-', '_'), convert_keys(v)) for (k, v) in data.items()])
    elif isinstance(data, list):
        return [convert_keys(i) for i in data]
    else:
        return data


class JSONAPIMixin(object):

    @classmethod
    def json_api_name(self):
        return inflection.underscore(inflection.pluralize(self.__name__)).replace('_', '-')

    @classmethod    
    def from_dict(self, data, dbsession):
        if hasattr(self, '__create_schema__'):
            data = self.__create_schema__.to_python(convert_keys(data),
                                                    State(dbsession=dbsession))
            obj = self()
            if 'relationships' in data:
                for key, value in data['relationships'].items():
                    if hasattr(obj, key):
                        if isinstance(value['data'], dict):
                            rel_class = COMPONENTS[value['data']['type']]['class']
                            rel = dbsession.query(rel_class).filter(rel_class.id == value['data']['id']).first()
                            if rel:
                                setattr(obj, key, rel)
                            else:
                                raise Invalid('Relationship target "%s" with id "%s" does not exist' % (value['data']['type'], value['data']['id']), value, None)
            if 'attributes' in data:
                for key, value in data['attributes'].items():
                    if hasattr(obj, key) and value != DoNotStore:
                        setattr(obj, key, value)
            return obj
        else:
            return None

    def update_from_dict(self, data, dbsession):
        if hasattr(self, '__update_schema__'):
            data = self.__update_schema__.to_python(convert_keys(data),
                                                    State(dbsession=dbsession))
            if 'relationships' in data:
                for key, value in data['relationships'].items():
                    if hasattr(self, key):
                        if isinstance(value['data'], dict):
                            rel_class = COMPONENTS[value['data']['type']]['class']
                            rel = dbsession.query(rel_class).filter(rel_class.id == value['data']['id']).first()
                            if rel:
                                setattr(self, key, rel)
                            else:
                                raise Invalid('Relationship target "%s" with id "%s" does not exist' % (value['data']['type'], value['data']['id']), value, None)
            if 'attributes' in data:
                for key, value in data['attributes'].items():
                    if hasattr(self, key) and value != DoNotStore:
                        setattr(self, key, value)

    def as_dict(self, request=None, depth=1):
        data = {'id': self.id,
                'type': self.__class__.__name__}
        # Set plain attributes
        if hasattr(self, '__json_attributes__'):
            data['attributes'] = {}
            for attr_name in self.__json_attributes__:
                data['attributes'][attr_name.replace('_', '-')] = getattr(self, attr_name)
        # Set computed attributes
        if hasattr(self, '__json_computed__'):
            if 'attributes' not in data:
                data['attributes'] = {}
            for attr_name in self.__json_computed__:
                data['attributes'][attr_name.replace('_', '-')] = getattr(self, attr_name)(request)
        # Set relationships
        if hasattr(self, '__json_relationships__'):
            data['relationships'] = {}
            for rel_name in self.__json_relationships__:
                if isinstance(rel_name, tuple):
                    rel_name, force_include = rel_name
                else:
                    force_include = False
                if depth > 0 or force_include:
                    # Include related ids
                    data['relationships'][rel_name.replace('_', '-')] = {'data': []}
                    try:
                        for rel in getattr(self, rel_name):
                            if rel and rel.allow(request.current_user, 'view'):
                                data['relationships'][rel_name.replace('_', '-')]['data'].append({'id': rel.id,
                                                                                                  'type': rel.__class__.__name__})
                    except:
                        rel = getattr(self, rel_name)
                        if rel and rel.allow(request.current_user, 'view'):
                            data['relationships'][rel_name.replace('_', '-')]['data'] = {'id': rel.id,
                                                                                         'type': rel.__class__.__name__}
                    if not data['relationships'][rel_name.replace('_', '-')]['data']:
                        del data['relationships'][rel_name.replace('_', '-')]
                else:
                    # Include link to load data
                    data['relationships'][rel_name.replace('_', '-')] = {'links': {'related': request.route_url('api.item.relationship',
                                                                                                                model=self.__class__.json_api_name(),
                                                                                                                iid=self.id,
                                                                                                                rid=rel_name)}}
        included = []
        # Handle included data
        if hasattr(self, '__json_relationships__'):
            for rel_name in self.__json_relationships__:
                if isinstance(rel_name, tuple):
                    rel_name, force_include = rel_name
                else:
                    force_include = False
                if depth > 0 or force_include:
                    try:
                        for rel in getattr(self, rel_name):
                            if rel and rel.allow(request.current_user, 'view'):
                                rel_data, rel_included = rel.as_dict(request=request,
                                                                     depth=depth - 1)
                                included.append(rel_data)
                                if rel_included:
                                    included.extend(rel_included)
                    except:
                        rel = getattr(self, rel_name)
                        if rel and rel.allow(request.current_user, 'view'):
                            rel_data, rel_included = rel.as_dict(request=request,
                                                                 depth=depth - 1)
                            included.append(rel_data)
                            if rel_included:
                                included.extend(rel_included)
        return data, included
