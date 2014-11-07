import re
import uuid
import time
import logging

logger = logging.getLogger(__name__)

from nymms.schemas.types import TimestampType

from schematics.models import Model
from schematics.types import StringType, IPv4Type, UUIDType, IntType
import arrow


class Suppression(Model):
    CURRENT_VERSION = 2

    rowkey = UUIDType(default=uuid.uuid4)
    regex = StringType(required=True)
    created = TimestampType(default=time.time)
    disabled = TimestampType(required=False, serialize_when_none=False)
    expires = TimestampType(required=True)
    ipaddr = IPv4Type(required=True)
    userid = StringType(required=True)
    comment = StringType(required=True)
    version = IntType(default=CURRENT_VERSION)

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
