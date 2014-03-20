import logging
import traceback
import time
import uuid

logger = logging.getLogger(__name__)

class ReactorFilter(object):
    def __init__(self, item):
        self.regex = str(item['regex'])
        self.expires = int(str(item['expires']))
        self.userid = str(item['userid'])
        self.ipaddr = str(item['ipaddr'])
        self.comment = str(item['comment'])
        self.uuid = str(item['key'])

    def to_dict(self):
        return {'regex': self.regex,
                'expires': str(self.expires),
                'userid': self.userid,
                'ipaddr': self.ipaddr,
                'comment': self.comment
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
        if self.domain.put_attributes(rowkey, {'regex': regex,
            'expires': expires,
            'comment': comment,
            'userid': userid,
            'ipaddr': ipaddr}):
            return rowkey
        else:
            return False

    def get_active_filters(self):
        """Returns a list of filters whichi are currently active in SDB"""
        now = int(time.time())
        return self.get_filters(now, 0)

    def get_filters(self, start, end):
        """Returns a list of filters which were active between start
        and end epoch"""
        self._setup_domain()
        query = "select * from `%s` where `expire` >= '%s' and `expire` <= '%s'" % (
                self._domain_name, start, end)
        filters = []
        for item in self.domain.select(query):
            filters.append(ReactorFilter(item))

        return filters
