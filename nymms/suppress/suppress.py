import time
import re
import logging

logger = logging.getLogger(__name__)


class ReactorSuppress(object):
    """Class wrapper around our SDB row's"""
    def __init__(self, item):
        self.regex = str(item['regex'])
        self.created_at = int(str(item['created_at']))
        self.expires = int(str(item['expires']))
        self.userid = str(item['userid'])
        self.ipaddr = str(item['ipaddr'])
        self.comment = str(item['comment'])
        self.rowkey = str(item['rowkey'])
        self.active = str(item['active'])
        self.re = re.compile(self.regex)


class SuppressFilterBackend(object):
    """Parent SuppressFilterBackend class.  Don't use this directly!

    You need to define:
    add_suppression(self, regex, expires, comment, userid, ipaddr)
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
        filters = self.get_cached_current_suppressions()
        for item in filters:
            if item.re.search(message):
                return item
        return False

    def add_suppression(self, **kwargs):
        raise NotImplementedError

    def get_suppressions(self, **kwargs):
        raise NotImplementedError

    def deactivate_suppression(self, **kwargs):
        raise NotImplementedError

    def deactivate_all_suppressions(self):
        """Deactivates all the active suppression filters we have currently."""
        for item in self.get_active_suppressions():
            logger.debug("Deactivating %s" % (rowkey,))
            self.deactivate_suppression(item.rowkey)
