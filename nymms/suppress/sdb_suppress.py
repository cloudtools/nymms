import logging
import traceback
import time
import uuid
from nymms.suppress.suppress import (SuppressFilterBackend, ReactorFilter)

logger = logging.getLogger(__name__)

class SDBSuppressFilterBackend(SuppressFilterBackend):
    def __init__(self, conn, timeout=60, domain_name='reactor_suppress'):
        self._conn = conn
        self._domain_name = domain_name
        self.domain = None
        logger.debug("%s initialized.", self.__class__.__name__)
        super(SDBSuppressFilterBackend, self).__init__(timeout)

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
            'rowkey': rowkey,
            'active': 'True'
            }):
            return rowkey
        else:
            return False

    def get_filters(self, expire, active=True):
        """Returns a list of filters which were active between start and end
        expire = expoch time
        active = True/False to limit to only filters flagged 'active' = 'True'
        """
        self._setup_domain()
        if start and end:
            query = "select * from `%s` where `expires` >= '%s'" % (
                    self._domain_name, expire)
        else:
            query = "select * from `%s` where `expires` > '0'" % (self._domain_name,)

        if active:
            query += " and `active` = 'True' order by expires"
        else:
            query += " order by expires"

        filters = []
        for item in self.domain.select(query):
            filters.append(ReactorFilter(item))

        return filters

    def delete_all_filters(self):
        """Deletes all the filters we have stored."""
        self._setup_domain()
        self._conn.delete_domain(self._domain_name)

    def deactivate_filter(self, rowkey):
        """Deactivates a single filter"""
        self._setup_domain()
        query = "select * from `%s` where `rowkey` = '%s'" % \
                (self._domain_name, rowkey)
        for item in self.domain.select(query):
            self._conn.put_attributes(self._domain_name,
                    rowkey, 
                    { 'active': int(time.time()) })
                    
