
COMPONENTS = {}


def register_component(cls, actions=None):
    global COMPONENTS
    component = {'class': cls}
    if actions:
        component['actions'] = actions
    COMPONENTS[cls.json_api_name()] = component
