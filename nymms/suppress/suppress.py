import time
import re


class ReactorFilter(object):
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
    add_filter(self, regex, expires, comment, userid, ipaddr)
    get_filters(self, expire, active)
    delete_all_filters(self)
    delete_filter(self, rowkey)
    """
    def __init__(self, timeout):
        self._filter_cache_timeout = timeout
        self._filter_cache_time = None
        self._cached_filters = []

    def get_active_filters(self):
        """Returns a list of filters which are currently active in SDB"""
        now = int(time.time())
        return self.get_filters(now, True)

    def get_cached_current_filters(self):
        """Returns a list of currently active suppression filters"""
        now = int(time.time())
        if not self._filter_cache_time:
            self._filter_cache_time = now - self._filter_cache_timeout

        if (self._filter_cache_time + self._filter_cache_timeout) <= now:
            self._filter_cache_time = now
            self._cached_filters = []
            filters = self.get_active_filters()
            for item in filters:
                self._cached_filters.append(item)

        return self._cached_filters

    def filtered_out(self, message):
        """Returns True if given message matches one of our active filters"""
        filters = self.get_cached_current_filters()
        for item in filters:
            if item.re.search(message):
                return True
        return False

    def add_filter(self, **kwargs):
        raise NotImplementedError

    def get_filters(self, **kwargs):
        raise NotImplementedError

    def deactivate_filter(self, **kwargs):
        raise NotImplementedError

    def delete_all_filters(self):
        raise NotImplementedError
