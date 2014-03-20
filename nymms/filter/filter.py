import time
import re


class ReactorFilter(object):
    def __init__(self, item):
        self.regex = str(item['regex'])
        self.created_at = int(str(item['created_at']))
        self.expires = int(str(item['expires']))
        self.userid = str(item['userid'])
        self.ipaddr = str(item['ipaddr'])
        self.comment = str(item['comment'])
        self.rowkey = str(item['rowkey'])
        self.re = re.compile(self.regex)

    def to_dict(self):
        return {'regex': self.regex,
                'created_at': str(self.created_at),
                'expires': str(self.expires),
                'userid': self.userid,
                'ipaddr': self.ipaddr,
                'comment': self.comment,
                'rowkey': self.rowkey
                }


class SuppressFilterBackend(object):
    """Parent SuppressFilterBackend class.  Don't use this directly!
    
    You need to define:
    add_filter(self, regex, expires, comment, userid, ipaddr)
    get_filters(self, start, end)
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
        return self.get_filters(now, 0)

    def get_cached_current_filters(self):
        """Returns a list of currently active suppression filters"""
        now = int(time.time())
        if not self._filter_cache_time:
            self._filter_cache_time = now
        if not self._cached_filters or \
                (self._filter_cache_time + self._filter_cache_timeout) < now:
            self._filter_cache_time = now
            self._cached_filters = []
            for item in self._suppress.get_active_filters():
                self._cached_filters.append(item)

        return self._cached_filters

    def filtered_out(self, message):
        """Returns True if the given message matches one of our active filters"""
        filters = self.get_cached_current_filters()
        for item in filters:
            if item.re.search(message):
                return True
        return False

    def add_filter(self, **kwargs):
        raise NotImplementedError

    def get_filters(self, **kwargs):
        raise NotImplementedError

    def delete_filter(self, **kwargs):
        raise NotImplementedError

    def delete_all_filters(self):
        raise NotImplementedError
