import logging
import copy

from nymms.exceptions import NymmsException

logger = logging.getLogger(__name__)


class ValidationError(NymmsException):
    def __init__(self, field, value):
        self.field = field
        self.value = value

    def __str__(self):
        return "Invalid value (%s) in field: %s" % (self.value, self.field,)


class MissingRequiredField(NymmsException):
    def __init__(self, field):
        self.field = field

    def __str__(self):
        return "Required field is blank: %s" % (self.field,)


class NymmsDataType(object):
    required_fields = []

    def __init__(self, object_id, origin=None):
        self.id = object_id
        self._origin = origin
        self._cleaned = {}

    def __str__(self):
        return "%s: %s" % (self.__class__.__name__, self.id)

    def validate(self):
        for field in self.required_fields:
            if getattr(self, field, None) is None:
                raise MissingRequiredField(field)
        for attr in dir(self):
            if attr.startswith('validate_'):
                validate_method = getattr(self, attr)
                if callable(validate_method):
                    validate_method()

    def delete(self):
        if self._origin:
            return self._origin.delete()

    def _serialize(self):
        """ Children classes should override this to update the dictionary
        returned by the serialize method.
        """
        return True

    def serialize(self, force=False):
        if self._cleaned and not force:
            return self._cleaned

        self.validate()
        for k, v in self.__dict__.iteritems():
            if not k.startswith('_'):
                self._cleaned[k] = v
        self._serialize()
        return self._cleaned

    @staticmethod
    def _deserialize(data):
        """ Children classes should override this to modify the dictionary
        that is used by the deserialize method.
        """
        return copy.deepcopy(data)

    @classmethod
    def deserialize(cls, data, origin=None):
        """ Produces a new data type object from a dictionary of data.  The
        origin object is passed in for further interactions with the system
        that the object was received from.  For example to delete the object
        out of a queue.
        """
        new_data = cls._deserialize(data)
        if not origin:
            origin = data
        object_id = new_data.pop('id')
        return cls(object_id, origin=origin, **new_data)
