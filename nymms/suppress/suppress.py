import time
import re
import logging
import uuid

from schematics.models import Model
from schematics.types import (StringType, IPv4Type, UUIDType, BaseType)
import arrow

logger = logging.getLogger(__name__)


class TimestampType(BaseType):
    def to_native(self, value, context=None):
        if isinstance(value, arrow.arrow.Arrow):
            return value
        return arrow.get(value)

    def to_primitive(self, value, context):
        return value.timestamp


class Suppression(Model):
    rowkey = UUIDType(default=uuid.uuid4)
    regex = StringType(required=True)
    created = TimestampType(default=time.time)
    disabled = TimestampType(required=False, serialize_when_none=False)
    expires = TimestampType(required=True)
    ipaddr = IPv4Type(required=True)
    userid = StringType(required=True)
    comment = StringType(required=True)

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


class SuppressFilterBackend(object):
    """Parent SuppressFilterBackend class.  Don't use this directly!

    You need to define:
    add_suppression(self, suppress)
    get_suppressions(self, expire, active)
    deactivate_suppression(self, rowkey)
    """
    def __init__(self, timeout):
        self._cache_timeout = timeout
        self._cache_expire_time = 0
        self._cached_suppressions = []

    def get_active_suppressions(self):
        """Returns a list of suppression filters which are currently
        active in SDB"""
        now = int(time.time())
        return self.get_suppressions(now, True)

    def get_cached_current_suppressions(self):
        """Returns a list of currently active suppression filters"""
        now = int(time.time())

        if self._cache_expire_time < now:
            logger.debug("Refreshing reactor suppression cache")
            self._cache_expire_time = now + self._cache_timeout
            self._cached_suppressions = []
            filters = self.get_active_suppressions()
            for item in filters:
                self._cached_suppressions.append(item)

        return self._cached_suppressions

    def is_suppressed(self, message):
        """Returns True if given message matches one of our active filters"""
        suppressions = self.get_cached_current_suppressions()
        for item in suppressions:
            if item.re.search(message):
                return item
        return False

    def add_suppression(self, suppress):
        raise NotImplementedError

    def get_suppressions(self, expire, active=True):
        raise NotImplementedError

    def deactivate_suppression(self, rowkey):
        raise NotImplementedError

    def deactivate_all_suppressions(self):
        """Deactivates all the active suppression filters we have currently."""
        deactivated = []
        for item in self.get_active_suppressions():
            logger.debug("Deactivating %s", item.rowkey)
            deactivated.append(item.rowkey)
            self.deactivate_suppression(item.rowkey)
        return deactivated
