import logging
import time
from nymms.suppress.suppress import SuppressFilterBackend, ReactorSuppress
from nymms.utils.aws_helper import ConnectionManager

logger = logging.getLogger(__name__)


class SDBSuppressFilterBackend(SuppressFilterBackend):
    def __init__(self, region, timeout=60, domain_name='nymms_suppress'):
        self.region = region
        self.domain_name = domain_name

        self._conn = None
        self._domain = None

        super(SDBSuppressFilterBackend, self).__init__(timeout)
        logger.debug("%s initialized.", self.__class__.__name__)

    @property
    def conn(self):
        if not self._conn:
            self._conn = ConnectionManager(self.region)
        return self._conn

    @property
    def domain(self):
        if not self._domain:
            self._domain = self.conn.sdb.create_domain(self.domain_name)
        return self._domain

    def add_suppression(self, suppress):
        """Adds a suppression filter to the SDB store
        """
        self.domain.put_attributes(suppress.rowkey, suppress.dict())
        logger.debug("Added %s to %s", suppress.rowkey, self.domain_name)
        return suppress.rowkey

    def get_suppressions(self, expire, active=True):
        """Returns a list of suppression filters which were active between
        start and end

        expire = expoch time
        active = True/False to limit to only filters flagged 'active' = 'True'
        """
        if expire:
            query = "select * from `%s` where `expires` >= '%s'" % (
                    self.domain_name, expire)
        else:
            query = "select * from `%s` where `expires` > '0'" % (
                    self.domain_name,)

        if active:
            query += " and `active` = 'True'"
        query += " order by expires"

        suppressors = []
        for item in self.domain.select(query):
            suppressors.append(ReactorSuppress(item))

        return suppressors

    def deactivate_suppression(self, rowkey):
        """Deactivates a single suppression filter"""
        self.conn.sdb.put_attributes(self.domain_name, rowkey,
                                     {'active': int(time.time())})
