"""
#########################################################
:mod:`~webrpg.scripts.populate` - Database initialisation
#########################################################

Implements the database initialisation functionality.

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
from alembic import command, config
from pyramid.paster import (get_appsettings, setup_logging)
from sqlalchemy import engine_from_config

from webrpg.models import (Base, DB_VERSION)


def init(subparsers):
    """Adds the sub-parser for the database initialisation."""
    parser = subparsers.add_parser('initialise-database', help='Initialise the database')
    parser.add_argument('configuration', help='WebRPG configuration file')
    parser.add_argument('--drop-existing', action='store_true', default=False, help='Drop any existing tables')
    parser.set_defaults(func=initialise_database)
    parser = subparsers.add_parser('update-database', help='Update the Web Teaching Environment database')
    parser.add_argument('configuration', help='Configuration file')
    parser.set_defaults(func=update_database)
    parser = subparsers.add_parser('downgrade-database', help='Downgrade the Web Teaching Environment database')
    parser.add_argument('configuration', help='Configuration file')
    parser.set_defaults(func=downgrade_database)


def initialise_database(args):
    """Initialise the database."""
    from webrpg.components import character, chat_message, game, map, session, user  # noqa
    settings = get_appsettings(args.configuration)
    setup_logging(args.configuration)
    engine = engine_from_config(settings, 'sqlalchemy.')
    if args.drop_existing:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    alembic_config = config.Config(args.configuration, ini_section='app:main')
    alembic_config.set_section_option('app:main', 'script_location', 'webrpg:migrations')
    command.stamp(alembic_config, "head")


def update_database(args):
    alembic_config = config.Config(args.configuration, ini_section='app:main')
    alembic_config.set_section_option('app:main', 'script_location', 'webrpg:migrations')
    command.upgrade(alembic_config, DB_VERSION)


def downgrade_database(args):
    alembic_config = config.Config(args.configuration, ini_section='app:main')
    alembic_config.set_section_option('app:main', 'script_location', 'webrpg:migrations')
    command.downgrade(alembic_config, '-1')
