import time
import re
import logging
import uuid

logger = logging.getLogger(__name__)


class ReactorSuppress(object):
    """Record of the suppression to store in SDB/etc"""
    def __init__(self, item):
        self.comment = str(item['comment'])
        self.expires = int(item['expires'])
        self.ipaddr = str(item['ipaddr'])
        self.regex = str(item['regex'])
        self.re = re.compile(self.regex)
        self.userid = str(item['userid'])
        self.rowkey = str(item.get('rowkey', uuid.uuid4()))
        self.active = str(item.get('active', True))
        self.created_at = int(item.get('created_at', time.time()))

    def dict(self):
        return {
                'active': self.active,
                'comment': self.comment,
                'created_at': self.created_at,
                'expires': self.expires,
                'ipaddr': self.ipaddr,
                'regex': self.regex,
                'userid': self.userid,
                'rowkey': self.rowkey
                }


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

    def get_suppressions(self, **kwargs):
        raise NotImplementedError

    def deactivate_suppression(self, **kwargs):
        raise NotImplementedError

    def deactivate_all_suppressions(self):
        """Deactivates all the active suppression filters we have currently."""
        deactivated = []
        for item in self.get_active_suppressions():
            logger.debug("Deactivating %s", item.rowkey)
            deactivated.append(item.rowkey)
            self.deactivate_suppression(item.rowkey)
        return deactivated
