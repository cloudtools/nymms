import logging
import traceback
import time
import uuid

logger = logging.getLogger(__name__)

class ReactorFilter(object):
    def __init__(self, item):
        self.regex = str(item['regex'])
        self.created_at = int(str(item['created_at']))
        self.expires = int(str(item['expires']))
        self.userid = str(item['userid'])
        self.ipaddr = str(item['ipaddr'])
        self.comment = str(item['comment'])
        self.rowkey = str(item['rowkey'])

    def to_dict(self):
        return {'regex': self.regex,
                'created_at': str(self.created_at),
                'expires': str(self.expires),
                'userid': self.userid,
                'ipaddr': self.ipaddr,
                'comment': self.comment,
                'rowkey': self.rowkey
                }

class ReactorSuppress(object):
    def __init__(self, conn, domain_name='reactor_suppress'):
        self._conn = conn
        self._domain_name = domain_name
        self.domain = None
        logger.debug("%s initialized.", self.__class__.__name__)

    def _setup_domain(self):
        if self.domain:
            return
        logger.debug("setting up reactor suppression domain %s",
                self._domain_name)
        self.domain = self._conn.create_domain(self._domain_name)


    def add_filter(self, regex, expires, comment, userid, ipaddr):
        """Adds a filter to the SDB store

        regex = regex to match against the NYMMS event key
        expire = number of seconds this filter should be active
        comment = Why you added this filter
        userid = userid of user creating this filter 
        ipaddr = IP address of host creating this filter 
        """
        self._setup_domain()
        rowkey = uuid.uuid4()
        if self.domain.put_attributes(rowkey, {
            'regex': regex,
            'created_at': int(time.time()),
            'expires': expires,
            'comment': comment,
            'userid': userid,
            'ipaddr': ipaddr,
            'rowkey': rowkey
            }):
            return rowkey
        else:
            return False

    def get_active_filters(self):
        """Returns a list of filters whichi are currently active in SDB"""
        now = int(time.time())
        return self.get_filters(now, 0)

    def get_filters(self, start=None, end=None):
        """Returns a list of filters which were active between start and end
        start / end = epoch time
        pass in 'None' and we'll return *all* filters
        """
        self._setup_domain()
        if start and end:
            query = "select * from `%s` where `expires` >= '%s' and `expires` <= '%s'" % (
                    self._domain_name, start, end)
        else:
            query = "select * from `%s`" % (self._domain_name,)
        query += " order by expires"
        filters = []
        for item in self.domain.select(query):
            filters.append(ReactorFilter(item))

        return filters

    def delete_all_filters(self):
        self._setup_domain()
        self._conn.delete_domain(self._domain_name)

    def delete_filter(self, rowkey):
        self._setup_domain()
        self.domain.delete_itme(rowkey)
