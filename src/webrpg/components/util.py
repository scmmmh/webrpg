# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""

from formencode import schema

from webrpg.models import (DBSession, User)

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


class EmberSchema(schema.Schema):
    
    allow_extra_fields = True
    filter_extra_fields = True

 