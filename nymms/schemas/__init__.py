import re
import uuid
import logging

logger = logging.getLogger(__name__)

from nymms.schemas.types import (TimestampType, StateType, StateTypeType,
                                 JSONType, StateNameType, StateTypeNameType)

from schematics.models import Model
from schematics.transforms import blacklist
from schematics.types import (
    StringType, IPv4Type, UUIDType, IntType)
import arrow


class OriginModel(Model):
    def __init__(self, raw_data=None, deserialize_mapping=None, strict=True,
                 origin=None):
        super(OriginModel, self).__init__(
            raw_data=raw_data,
            deserialize_mapping=deserialize_mapping,
            strict=strict)
        self._origin = origin


class Suppression(OriginModel):
    CURRENT_VERSION = 2

    rowkey = UUIDType(default=uuid.uuid4)
    regex = StringType(required=True)
    created = TimestampType(default=arrow.get)
    disabled = TimestampType(serialize_when_none=False)
    expires = TimestampType(required=True)
    ipaddr = IPv4Type(required=True)
    userid = StringType(required=True)
    comment = StringType(required=True)
    version = IntType(default=CURRENT_VERSION)

    default_sort_order = 'created'
    pk = 'rowkey'

    @property
    def active(self):
        if self.disabled or self.expires < arrow.get():
            return False
        else:
            return True

    @property
    def state(self):
        if self.disabled:
            return "disabled (%s, %s)" % (self.disabled,
                                          self.disabled.humanize())
        elif self.expires < arrow.get():
            return "expired (%s, %s)" % (self.expires,
                                         self.expires.humanize())
        else:
            return "active"

    @property
    def re(self):
        return re.compile(self.regex)

    @classmethod
    def migrate(cls, item):
        """ Takes an old version 1 item and returns a new version 2
        Suppression.
        """
        new_suppression = None
        try:
            new_suppression = cls({
                'rowkey': uuid.UUID(item['rowkey']),
                'regex': item['regex'],
                'created': arrow.get(int(item['created_at'])),
                'expires': arrow.get(int(item['expires'])),
                'ipaddr': item['ipaddr'],
                'userid': item['userid'],
                'comment': item['comment']})
            if not item['active'] == 'True':
                new_suppression.disabled = arrow.get(int(item['active']))
        except Exception:
            logger.exception("Unable to migrate suppression to v2: %s", item)
        return new_suppression


class APISuppression(Suppression):
    """Suppression Model with friendler date fields.
    """
    disabled = TimestampType(serialize_when_none=True)


class StateModel(Model):
    CURRENT_VERSION = 2

    state = StateType(required=True)
    state_type = StateTypeType(required=True)
    version = IntType(default=CURRENT_VERSION)

    @property
    def state_name(self):
        return self.state.name

    @property
    def state_type_name(self):
        return self.state_type.name


class Task(OriginModel):
    id = StringType(required=True)
    created = TimestampType(default=arrow.get)
    attempt = IntType(default=0)
    context = JSONType()

    def increment_attempt(self):
        self.attempt += 1


class Result(StateModel, OriginModel):
    id = StringType(required=True)
    timestamp = TimestampType(default=arrow.get)
    output = StringType()
    task_context = JSONType()

    class Options:
        roles = {'strip_context': blacklist('task_context')}


class APIResult(Result):
    """Result model with friendlier fields for input/output
    """
    state = StateNameType(required=True)
    state_type = StateTypeNameType(required=True)


class StateRecord(StateModel, OriginModel):
    id = StringType(required=True)
    last_update = TimestampType(default=arrow.get)
    last_state_change = TimestampType(default=arrow.get)

    pk = 'id'
    default_sort_order = 'last_update'

    @classmethod
    def migrate(cls, item):
        new_state = None
        try:
            new_state = cls({
                'id': item['id'],
                'last_update': arrow.get(int(item['last_update'])),
                'last_state_change': arrow.get(int(item['last_state_change'])),
                'state': item['state'],
                'state_type': item['state_type']})
        except Exception:
            logger.exception("Unable to migrate state record to v2: %s", item)
        return new_state


class APIStateRecord(StateRecord):
    """StateRecord model with friendlier fields for input/output
    """
    state = StateNameType(required=True)
    state_type = StateTypeNameType(required=True)
