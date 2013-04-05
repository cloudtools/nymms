from weakref import WeakValueDictionary

from nymms import exceptions

class DuplicateEntryError(exceptions.NymmsException):
    def __init__(self, name, obj, registry):
        self.name = name
        self.obj = obj
        self.registry = registry

    def __str__(self):
        return "Duplicate entry in '%s' registry for '%s'." % (
                self.registry._object_type.__name__, self.name)


class Registry(WeakValueDictionary):
    def __init__(self, object_type, *args, **kwargs):
        self._object_type = object_type
        WeakValueDictionary.__init__(self, *args, **kwargs)

    def __setitem__(self, name, value):
        if not isinstance(value, self._object_type):
            raise TypeError("This registry only accepts objects of type %s." %
                    (self._object_type.__name__))

        if self.has_key(name):
            raise DuplicateEntryError(name, value, self)
        WeakValueDictionary.__setitem__(self, name, value)
