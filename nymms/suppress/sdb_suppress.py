import logging
import traceback
import time
from nymms.suppress.suppress import SuppressFilterBackend, ReactorSuppress

logger = logging.getLogger(__name__)


class SDBSuppressFilterBackend(SuppressFilterBackend):
    def __init__(self, conn, timeout=60, domain_name='nymms_suppress'):
        self._conn = conn
        self._domain_name = domain_name
        self.domain = None
        super(SDBSuppressFilterBackend, self).__init__(timeout)
        logger.debug("%s initialized.", self.__class__.__name__)

    def _setup_domain(self):
        if self.domain:
            return
        logger.debug("setting up reactor suppression domain %s",
                self._domain_name)
        self.domain = self._conn.create_domain(self._domain_name)

    def add_suppression(self, suppress):
        """Adds a suppression filter to the SDB store
        """
        self._setup_domain()
        self.domain.put_attributes(suppress.rowkey, suppress.dict())
        logger.debug("Added %s to %s", suppress.rowkey, self._domain_name)
        return suppress.rowkey

    def get_suppressions(self, expire, active=True):
        """Returns a list of suppression filters which were active between
        start and end

        expire = expoch time
        active = True/False to limit to only filters flagged 'active' = 'True'
        """
        self._setup_domain()
        if expire:
            query = "select * from `%s` where `expires` >= '%s'" % (
                    self._domain_name, expire)
        else:
            query = "select * from `%s` where `expires` > '0'" % (
                    self._domain_name,)

        if active:
            query += " and `active` = 'True'"
        query += " order by expires"

        suppressors = []
        for item in self.domain.select(query):
            suppressors.append(ReactorSuppress(item))

        return suppressors

    def deactivate_suppression(self, rowkey):
        """Deactivates a single suppression filter"""
        self._setup_domain()
        self._conn.put_attributes(self._domain_name, rowkey,
                {'active': int(time.time())})
