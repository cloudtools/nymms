import logging

from nymms.schemas import Suppression

import arrow

logger = logging.getLogger(__name__)


class SuppressionManager(object):
    """Parent SuppressFilterBackend class.  Don't use this directly!

    You need to define:
    add_suppression(self, suppress)
    get_suppressions(self, expire, include_disabled)
    deactivate_suppression(self, rowkey)
    """
    def __init__(self, cache_ttl, schema_class):
        self.cache_ttl = cache_ttl
        self._cache_expire_time = 0
        self._cached_suppressions = []
        self._backend = None
        self.schema_class = schema_class
        logger.debug("%s initialized.", self.__class__.__name__)

        self.migrate_suppressions()

    @property
    def backend(self):
        if not self._backend:
            self._backend = self.get_backend()
        return self._backend

    def deserialize(self, item, strict=False):
        try:
            item_obj = self.schema_class(item, strict=strict, origin=item)
            item_obj.validate()
            return item_obj
        except Exception:
            logger.exception("Problem deserializing item:")
            logger.error("Data: %s", str(item))
            return None

    def get_active_suppressions(self, now=None):
        """Returns a list of suppression filters which are currently
        active in SDB"""
        now = now or arrow.get()
        # return the suppressions only, not the token
        return self.get_suppressions(now, include_disabled=False)[0]

    def cache_expired(self, now=None):
        now = now or arrow.get()
        return self._cache_expire_time < now.timestamp

    def refresh_cache(self, now=None):
        logger.debug("Refreshing reactor suppression cache")
        now = now or arrow.get()
        self._cache_expire_time = now.timestamp + self.cache_ttl
        self._cached_suppressions = []
        for suppression in self.get_active_suppressions():
            self._cached_suppressions.append(suppression)

    def get_current_suppressions(self, now=None):
        """Returns a list of currently active suppression filters"""
        now = now or arrow.get()
        if self.cache_expired(now):
            self.refresh_cache(now)
        return self._cached_suppressions

    def is_suppressed(self, message, now=None):
        """Returns True if given message matches one of our active filters"""
        now = now or arrow.get()
        suppressions = self.get_current_suppressions(now)
        for item in suppressions:
            if item.re.search(message):
                return item
        return False

    def get_backend(self, *args, **kwargs):
        raise NotImplementedError

    def add_suppression(self, suppression):
        """Adds a suppression filter to the SDB store
        """
        self.backend.put(suppression)
        return suppression.rowkey

    def get_suppressions(self, expire=None, include_disabled=False,
                         limit=None):
        """ Gets all suppressions that expire after given 'expire' time. """
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

    def get(self, suppression_id):
        item = self.backend.get(suppression_id)
        if item:
            return self.deserialize(item)
        return None

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
            self.backend.purge_suppression(old_key)
            if new_suppression:
                logger.debug("Migrating old suppression %s.", old_key)
                self.add_suppression(new_suppression)

    def filter(self, *args, **kwargs):
        result, next_token = self.backend.filter(*args, **kwargs)
        return ([self.deserialize(s) for s in result], next_token)
