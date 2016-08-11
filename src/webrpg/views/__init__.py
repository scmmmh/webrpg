"""
#################################
:mod:`~webrpg.views` - Core views
#################################

Core views for loading the WebRPG Ember application.

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config


def init(config):
    """Initialise the core routes."""
    from . import api

    config.add_route('root', '/')
    config.add_static_view('gui', 'webrpg:gui', cache_max_age=3600)
    api.init(config)


@view_config(route_name='root')
def root(request):
    """Handle the route request by re-directing to the static "gui/index.html"."""
    raise HTTPFound(request.static_url('webrpg:gui/index.html'))
