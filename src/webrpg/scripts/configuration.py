# -*- coding: utf-8 -*-
"""
Script used to generate a configuration file.

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""
import uuid

from pkg_resources import resource_string

from webrpg.scripts.main import get_user_parameter


def init(subparsers):
    parser = subparsers.add_parser('generate-config', help='Generate the WebRPG configuration file')
    parser.add_argument('--filename', default='production.ini', help='Configuration file name')
    parser.add_argument('--sqla-connection-string', default=None, help='SQLAlchemy database connection string')
    parser.set_defaults(func=generate_config)

    
def generate_config(args):
    '''Generates a configuration file based on the default_config.txt template.
    '''
    default_config = resource_string('webrpg', 'scripts/templates/default_config.txt').decode('utf-8')
    if args.sqla_connection_string:
        default_config = default_config.replace('%(sqlalchemy_url)s', args.sqla_connection_string)
    else:
        default_config = default_config.replace('%(sqlalchemy_url)s', get_user_parameter('SQL Alchemy Connection String', 'sqlite:///%(here)s/pyire_test.db'))
    
    with open(args.filename, 'w') as out_f:
        out_f.write(default_config)
    