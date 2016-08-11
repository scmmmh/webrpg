"""
########################################
:mod:`~webrpg` - Web-based RPG interface
########################################

The main package for the WebRPG system.

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from . import views
from .models import (DBSession, Base)


def main(global_config, **settings):
    """Initialises and returns the WebRPG Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(settings=settings)
    config.add_static_view('static', 'static', cache_max_age=3600)
    views.init(config)
    config.scan()
    return config.make_wsgi_app()
