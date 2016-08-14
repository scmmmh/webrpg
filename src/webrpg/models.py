"""
############################################
:mod:`~webrpg.models` - Database foundations
############################################

Provides the :data:`~webrpg.models.DBSession` for database access and the
:class:`~webrpg.models.JSONAPIMixin` that provides the functionality for
exposing a model via a JSON API.

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
import inflection
import json

from formencode import Invalid
from sqlalchemy import text, UnicodeText
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.ext.declarative import (declarative_base)
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import (scoped_session, sessionmaker)
from sqlalchemy.types import TypeDecorator
from zope.sqlalchemy import ZopeTransactionExtension

from webrpg.components import COMPONENTS
from webrpg.util import State, DoNotStore

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

DB_VERSION = 'b7872d9773e4'


class DBUpgradeException(Exception):
    """The :class:`~webrpg.models.DBUpgradeException` is used to indicate that
    the database requires an upgrade before the WebRPG system
    can be used.
    """
    def __init__(self, current, required):
        self.current = current
        self.required = required

    def __repr__(self):
        return "DBUpgradeException('%s', '%s'" % (self.current, self.required)

    def __str__(self):
        return "A database upgrade is required.\n\n" + \
            "You are currently running version '%s', but version '%s' is " % (self.current, self.required) + \
            " required. Please run WebRPG update-database config.ini upgrade to upgrade the database " + \
            "and then start the application again."


def check_database_version():
    """Checks that the current version of the database matches the version specified
    by ``DB_VERSION``. This requires the use of the Alembic database migration library.
    """
    dbsession = DBSession()
    try:
        inspector = Inspector.from_engine(dbsession.bind)
        if 'alembic_version' in inspector.get_table_names():
            result = dbsession.query('version_num').\
                from_statement(text('SELECT version_num FROM alembic_version WHERE version_num = :version_num')).\
                params(version_num=DB_VERSION).first()
            if not result:
                result = dbsession.query('version_num').\
                    from_statement('SELECT version_num FROM alembic_version').first()
                raise DBUpgradeException(result[0], DB_VERSION)
    except OperationalError:
        raise DBUpgradeException('No version-information found', DB_VERSION)


def convert_keys(data):
    """Converts all keys in the ``data`` to JSON API needs ('-' instead of '_').

    :param data: The data to convert
    :return: The converted data
    """
    if isinstance(data, dict):
        return dict([(k.replace('-', '_'), convert_keys(v)) for (k, v) in data.items()])
    elif isinstance(data, list):
        return [convert_keys(i) for i in data]
    else:
        return data


class JSONAPIMixin(object):
    """Mixin that provides the necessary functions for integrating an SQLAlchemy model
    into a JSON API interface. To use the mixin, the following attributes need to be
    defined on the class:

    * ``__create_schema__``:
    * ``__update_schema__``:
    * ``__json_attributes__``: List of attribute names to include in the resulting JSON
    * ``__json_computed__``: List of function properties to include as attributes in the resulting JSON
    * ``__json_relationships__``: List of relationships to include as relationships in the JSON
    """

    @classmethod
    def json_api_name(self):
        """Converts the class name into a JSON API representation."""
        return inflection.underscore(inflection.pluralize(self.__name__)).replace('_', '-')

    @classmethod
    def from_dict(self, data, dbsession):
        """Construct a new instance of the model based on the JSON ``data`` dictionary. Will
        only construct a new instance if the class has a ``__create_schema__`` attribute and
        the ``data`` validates against that schema.

        :param data: The data to use for the new instance
        :type data: ``dict``
        :param dbsession`: Database session to use for linking relationships
        :type dbsession: :data:`~webrpg.models.DBSession`
        :return: The new instance of the class
        """
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
        """Update the instance using the ``data``. Will only update if the class has a
        ``__update_schema__`` and the ``data`` validates against that schema.

        :param data: The data to use for updating
        :type data: ``dict``
        :param dbsession`: Database session to use for linking relationships
        :type dbsession: :data:`~webrpg.models.DBSession`
        """
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
        """Convert this instance to a JSON API representation. What is output depends on the following properties:

        * ``__json_attributes__``: List of attribute names to include in the resulting JSON
        * ``__json_computed__``: List of function properties to include as attributes in the resulting JSON
        * ``__json_relationships__``: List of relationships to include as relationships in the JSON

        If the ``depth`` is greater than 0, it will recursively include relationship objects in the response. Additionally
        if the relationship name is a tuple ``(name, True)`` then this will always be included, regardless of ``depth``.

        :param request: Request to use for building URLs
        :type request: :class:`~pyramid.request.Request`
        :param depth: Depth of recursive inclusion (default: 1)
        :type depth: ``int``
        :return: The JSON API representation of this instance
        :rtype: ``dict``
        """
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


class JSONUnicodeText(TypeDecorator):
    """The class:`~pywebtools.models.JSONUnicodeText` is an extension to the
    :class:`~sqlalchemy.UnicodeText` column type that does automatic conversion
    from the JSON string representation stored in the DB to a dict/list representation
    for use in python.
    """

    impl = UnicodeText

    def process_bind_param(self, value, dialect):
        """Convert the dict/list to JSON for storing.
        """
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        """Convert the JSON to dict/list for use.
        """
        if value is not None:
            value = json.loads(value)
        return value
