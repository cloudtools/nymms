import logging
import uuid

from nymms.suppress.suppress import SuppressFilterBackend, Suppression
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
        self.domain.put_attributes(suppress.rowkey, suppress.to_primitive())
        logger.debug("Added %s to %s", suppress.rowkey, self.domain_name)
        return suppress.rowkey

    def migrate_suppressions(self):
        """ Temporary method, used to update all expressions to the new format
        using schematics & arrow.
        """
        query = "select * from `%s` where `created_at` is not null" % (
            self.domain_name)
        for item in self.domain.select(query, consistent_read=True):
            new_suppression = None
            try:
                new_suppression = Suppression({
                    'rowkey': uuid.UUID(item['rowkey']),
                    'regex': item['regex'],
                    'created': arrow.get(int(item['created_at'])),
                    'expires': arrow.get(int(item['expires'])),
                    'ipaddr': item['ipaddr'],
                    'userid': item['userid'],
                    'comment': item['comment']})
                if not item['active'] == 'True':
                    new_suppression.disabled = arrow.get(int(item['active']))
            except Exception:
                logger.warning("Skipping invalid suppression: %s", item)
            old_key = item['rowkey']
            item.delete()
            if new_suppression:
                logger.debug("Migrating old suppression %s.", old_key)
                self.add_suppression(new_suppression)

    def get_suppressions(self, expire, active=True):
        """Returns a list of suppression filters which were active between
        start and end

        expire = expoch time
        active = True/False to limit to only filters flagged 'active' = 'True'
        """
        self.migrate_suppressions()
        if expire:
            query = "select * from `%s` where `expires` >= '%s'" % (
                    self.domain_name, expire.timestamp)
        else:
            query = "select * from `%s` where `expires` > '0'" % (
                    self.domain_name,)

        query += " and `created` is not null"

        if active:
            query += " and `disabled` is null"
        query += " order by `created`"

        logger.debug("Query: %s", query)

        suppressions = []
        for item in self.domain.select(query, consistent_read=True):
            try:
                suppressions.append(Suppression(item))
            except schematics.exceptions.ModelConversionError as e:
                logger.warning("Skipping invalid suppression: %s", item)
                logger.warning("    %s", e.message)
                continue

        return suppressions

    def deactivate_suppression(self, rowkey):
        """Deactivates a single suppression filter"""
        self.conn.sdb.put_attributes(self.domain_name, rowkey,
                                     {'disabled': arrow.get().timestamp})
