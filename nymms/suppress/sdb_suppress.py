import logging

from nymms.suppress.suppress import SuppressionManager
from nymms.schemas import Suppression
from nymms.providers.sdb import SimpleDBBackend

import arrow

logger = logging.getLogger(__name__)


class SDBSuppressionManager(SuppressionManager):
    def __init__(self, region, timeout=60, domain_name='nymms_suppress',
                 schema_class=Suppression):
        self.region = region
        self.domain_name = domain_name
        self.timeout = timeout

        super(SDBSuppressionManager, self).__init__(timeout, schema_class)

    @property
    def conn(self):
        return self.backend.conn

    @property
    def domain(self):
        return self.backend.domain

    def get_backend(self):
        return SimpleDBBackend(self.region, self.domain_name)

    def get_old_suppressions(self):
        query = ("select * from `%s` where `version` is null or "
                 "`version` < '%s'" % (self.backend.domain_name,
                                       Suppression.CURRENT_VERSION))
        return self.domain.select(query, consistent_read=True)

    def get_suppressions(self, expire=None, include_disabled=False,
                         limit=None):
        """ Returns a list of suppressions that are not expired.

        expire = arrow datetime, or None for no start time
        active = True/False to limit to only filters flagged 'active' = 'True'
        """
        filters = ["`created` is not null"]
        if expire:
            filters.append("`expires` >= '%s'" % expire.isoformat())
        else:
            filters.append("`expires` > '0'")

        if not include_disabled:
            filters.append("`disabled` is null")

        return self.filter(filters=filters, max_items=limit)

    def deactivate_suppression(self, rowkey):
        """Deactivates a single suppression"""
        if self.backend.get(rowkey):
            self.conn.sdb.put_attributes(self.backend.domain_name, rowkey,
                                         {'disabled': arrow.get().isoformat()})
            return True
        return False
