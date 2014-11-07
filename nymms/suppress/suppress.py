import logging

from nymms.schemas import Suppression

import arrow

logger = logging.getLogger(__name__)


class SuppressFilterBackend(object):
    """Parent SuppressFilterBackend class.  Don't use this directly!

    You need to define:
    add_suppression(self, suppress)
    get_suppressions(self, expire, active)
    deactivate_suppression(self, rowkey)
    """
    def __init__(self, timeout):
        self._cache_timeout = timeout
        self._cache_expire_time = 0
        self._cached_suppressions = []
        self.migrate_suppressions()

    def get_active_suppressions(self):
        """Returns a list of suppression filters which are currently
        active in SDB"""
        return self.get_suppressions(arrow.get(), True)

    def get_cached_current_suppressions(self):
        """Returns a list of currently active suppression filters"""
        now = arrow.get()

        if self._cache_expire_time < now.timestamp:
            logger.debug("Refreshing reactor suppression cache")
            self._cache_expire_time = now.timestamp + self._cache_timeout
            self._cached_suppressions = []
            filters = self.get_active_suppressions()
            for item in filters:
                self._cached_suppressions.append(item)

        return self._cached_suppressions

    def is_suppressed(self, message):
        """Returns True if given message matches one of our active filters"""
        suppressions = self.get_cached_current_suppressions()
        for item in suppressions:
            if item.re.search(message):
                return item
        return False

    def add_suppression(self, suppress):
        """ Adds a suppression to the SuppressionBackend."""
        raise NotImplementedError

    def get_suppressions(self, expire, active=True):
        """ Gets a single suppression from the SuppressionBackend."""
        raise NotImplementedError

    def deactivate_suppression(self, rowkey):
        """ Deactivates a suppression in the SuppressionBackend."""
        raise NotImplementedError

    def get_old_suppressions(self):
        """ Gets all suppressions in the SuppressionBackend that are not the
        current version. The current_version can be gotten from
        nymms.schemas.Suppression.CURRENT_VERSION
        """
        raise NotImplementedError

    def purge_suppression(self, key):
        """ Given the key of a suppression, totally deletes it from the
        SuppressionBackend. deactivate_suppresion should be used instead in
        most cases, this is primarily used when migrating from old versions
        of Suppressions to new versions (ie: in migrate_suppressions)
        """
        raise NotImplementedError

    def deactivate_all_suppressions(self):
        """Deactivates all the active suppression filters we have currently."""
        deactivated = []
        for item in self.get_active_suppressions():
            logger.debug("Deactivating %s", item.rowkey)
            deactivated.append(item.rowkey)
            self.deactivate_suppression(item.rowkey)
        return deactivated

    def migrate_suppressions(self):
        """ Temporary method, used to update all expressions to the new format
        using schematics & arrow.
        """
        for item in self.get_old_suppressions():
            new_suppression = Suppression.migrate(item)
            old_key = item['rowkey']
            self.purge_suppression(old_key)
            if new_suppression:
                logger.debug("Migrating old suppression %s.", old_key)
                self.add_suppression(new_suppression)
