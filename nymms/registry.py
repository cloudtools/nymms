import logging

from nymms import exceptions

logger = logging.getLogger(__name__)


class DuplicateEntryError(exceptions.NymmsException):
    def __init__(self, name, obj, registry):
        self.name = name
        self.obj = obj
        self.registry = registry

    def __str__(self):
        return "Duplicate entry in '%s' registry for '%s'." % (
            self.registry._object_type.__name__, self.name)


class Registry(dict):
    def __init__(self, object_type, *args, **kwargs):
        logging.debug("New '%s' registry id: %d" % (object_type, id(self)))
        self._object_type = object_type
        dict.__init__(self, *args, **kwargs)

    def __setitem__(self, name, value):
        if not isinstance(value, self._object_type):
            raise TypeError("This registry only accepts objects of "
                            "type %s." % (self._object_type.__name__))

        if name in self:
            raise DuplicateEntryError(name, value, self)
        dict.__setitem__(self, name, value)
