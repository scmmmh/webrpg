# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config


def init(config):
    from . import api
    
    config.add_route('root', '/')
    config.add_static_view('gui', 'webrpg:gui', cache_max_age=3600)
    api.init(config)


@view_config(route_name='root')
def handle_collection(request):
    raise HTTPFound(request.static_url('webrpg:gui/index.html'))
