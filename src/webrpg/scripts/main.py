"""
###############################################
:mod:`~webrpg.scripts.main` - Command-line Tool
###############################################

Implements the access point for the command-line tool.

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
from argparse import ArgumentParser


def get_user_parameter(prompt, default=''):
    """Get user input."""
    if default:
        prompt = '%s [%s]: ' % (prompt, default)
    else:
        prompt = '%s: ' % (prompt)
    response = input(prompt)
    if response.strip() == '':
        return default
    else:
        return response


def main():
    """Entry-point for the command-line tool."""
    from . import configuration, populate

    parser = ArgumentParser(description='WebRPG administration application')
    subparsers = parser.add_subparsers()

    configuration.init(subparsers)
    populate.init(subparsers)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_usage()
