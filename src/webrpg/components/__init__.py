"""
###########################################
:mod:`~webrpg.components` - Game Components
###########################################

Components implement the actual game functionality. In order to
be available via the JSON API (:class:`~webrpgs.views.api`) components
must be registered via :func:`~webrpg.components.register_component`.

.. moduleauthor:: Mark Hall <mark.hall@work.room3b.eu>
"""
COMPONENTS = {}


def register_component(cls, actions=None):
    """Register the ``cls`` as a JSON API component with the given ``actions``.

    :param cls: The component class to register
    :type cls: ``class``
    :param actions: The list of actions the component supports ("new", "list", "item", "update", "delete")
    :type actions: ``list``
    """
    global COMPONENTS
    component = {'class': cls}
    if actions:
        component['actions'] = actions
    COMPONENTS[cls.json_api_name()] = component
