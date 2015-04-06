import logging

from nymms.schemas.types import STATE_OK
from nymms.reactor.handlers.Handler import Handler
from nymms.utils.aws_helper import ConnectionManager


logger = logging.getLogger(__name__)


class SDBHandler(Handler):
    """ A basic handler to persist alerts to AWS simpleDB.  To filter
    results you should subclass this and provide a _filter method.

    config options:
      enabled: bool
      region: string, aws region (us-east-1, etc)
      sender: string, email address
      subject_template: string
      body_template: string
      recipients: list, email addresses
      filters: list, filters
    """

    def __init__(self, *args, **kwargs):
        super(SDBHandler, self).__init__(*args, **kwargs)
        self._conn = None
        self._domain = None
        self.region = self.config['region']
        self.domain_name = self.config['alerts_domain']

    @property
    def conn(self):
        if not getattr(self, '_aws_conn', None):
            self._conn = ConnectionManager(region=self.region)
        return self._conn

    @property
    def domain(self):
        if not self._domain:
            self._domain = self.conn.sdb.create_domain(self.domain_name)
        return self._domain

    def _save_result(self, result, previous_state):
        """Adds a result to the SDB store
        """
        item_name = '%s-%s' % (result.id, result.timestamp)
        # only persist alert states
        if result.state in (STATE_OK,):
            return item_name
        self.domain.put_attributes(item_name, result.to_primitive())
        logger.debug("Added %s to %s", item_name, self.domain_name)
        return item_name

    def _process(self, result, previous_state):
        self._save_result(result, previous_state)
