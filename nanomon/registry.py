class DuplicateEntryError(Exception):
    def __init__(self, name, obj, registry):
        self.name = name
        self.obj = obj
        self.registry = registry

    def __str__(self):
        return "Duplicate entry in '%s' registry for '%s'." % (
                self.registry._registry_name, self.name)


class Registry(dict):
    def __init__(self, registry_name, *args, **kwargs):
        self._registry_name = registry_name
        super(Registry, self).__init__(*args, **kwargs)

    def __setitem__(self, name, value):
        if self.has_key(name):
            raise DuplicateEntryError(name, value, self)
        dict.__setitem__(self, name, value)


monitoring_groups = Registry('monitoring_groups')
hosts = Registry('hosts')
monitors = Registry('monitors')
commands = Registry('commands')
