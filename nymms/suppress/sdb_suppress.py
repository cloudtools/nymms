import logging

from nymms.suppress.suppress import SuppressFilterBackend
from nymms.schemas import Suppression
from nymms.utils.aws_helper import ConnectionManager

import arrow
import schematics

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
        # filter out None, since simpleDB will write "None" instead of writing
        # a null value as you would expect.
        attributes = {
            k: v for k, v in suppress.to_primitive().items() if v is not None}
        self.domain.put_attributes(suppress.rowkey, attributes)
        logger.debug("Added %s to %s", suppress.rowkey, self.domain_name)
        return suppress.rowkey

    def get_old_suppressions(self):
        query = ("select * from `%s` where `version` is null or "
                 "`version` < '%s'" % (self.domain_name,
                                       Suppression.CURRENT_VERSION))
        return self.domain.select(query, consistent_read=True)

    def purge_suppression(self, key):
        """ This fully deletes the item from SDB. This is mostly used
        for migrations, and shouldn't be used in most cases. Instead you
        probably want deactivate_suppression().
        """
        self.domain.delete_attributes(key)

    def get_suppressions(self, expire, active=True, model_cls=Suppression,
                         limit=None):
        """Returns a list of suppression filters which were active between
        start and end

        expire = expoch time
        active = True/False to limit to only filters flagged 'active' = 'True'
        """
        query = "select * from `%s`" % self.domain_name
        where_clause = []
        if expire:
            where_clause.append("`expires` >= '%s'" % expire.timestamp)
        where_clause.append("`created` is not null")
        if active:
            where_clause.append('`disabled` is null')
        query += " where " + " and ".join(where_clause) + " order by `created`"

        logger.debug("Query for suppressions: %s", query)

        suppressions = []
        for item in self.domain.select(
                query, consistent_read=True, max_items=limit):
            try:
                suppressions.append(model_cls(item))
            except schematics.exceptions.ModelConversionError as e:
                logger.warning("Skipping invalid suppression: %s", item)
                logger.warning("    %s", e.message)
                continue

        return suppressions

    def deactivate_suppression(self, rowkey):
        """Deactivates a single suppression filter"""
        self.conn.sdb.put_attributes(self.domain_name, rowkey,
                                     {'disabled': arrow.get().timestamp})
