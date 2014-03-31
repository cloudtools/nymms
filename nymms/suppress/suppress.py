import time
import re
import logging

logger = logging.getLogger(__name__)


class ReactorSuppress(object):
    """Base class wrapper around our storage row"""
    def __init__(self, item):
        # set self.rowkey in your subclass!!!
        self.comment = str(item['comment'])
        self.expires = int(item['expires'])
        self.ipaddr = str(item['ipaddr'])
        self.regex = str(item['regex'])
        self.re = re.compile(self.regex)
        self.userid = str(item['userid'])

        if 'active' in item:
            self.active = str(item['active'])
        else:
            self.active = True

        if 'created_at' in item:
            self.created_at = int(str(item['created_at']))
        else:
            self.created_at = int(time.time())

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
        self._filter_cache_timeout = timeout
        self._filter_cache_time = None
        self._cached_filters = []

    def get_active_suppressions(self):
        """Returns a list of filters which are currently active in SDB"""
        now = int(time.time())
        return self.get_suppressions(now, True)

    def get_cached_current_suppressions(self):
        """Returns a list of currently active suppression filters"""
        now = int(time.time())
        if not self._filter_cache_time:
            self._filter_cache_time = now - self._filter_cache_timeout

        if (self._filter_cache_time + self._filter_cache_timeout) <= now:
            logger.debug("Refreshing reactor suppression cache")
            self._filter_cache_time = now
            self._cached_filters = []
            filters = self.get_active_suppressions()
            for item in filters:
                self._cached_filters.append(item)

        return self._cached_filters

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
        for item in self.get_active_suppressions():
            logger.debug("Deactivating %s", item.rowkey)
            self.deactivate_suppression(item.rowkey)
