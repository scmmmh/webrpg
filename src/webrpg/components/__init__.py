
COMPONENTS = {}


def register_component(name, cls, actions=None):
    global COMPONENTS
    component = {'class': cls}
    if actions:
        component['actions'] = actions
    COMPONENTS[name] = component
