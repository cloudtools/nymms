import logging

logger = logging.getLogger(__name__)

from boto.exception import SDBResponseError

from nymms.state.State import StateManager
from nymms.schemas import StateRecord
from nymms.exceptions import OutOfDateState
from nymms.providers.sdb import SimpleDBBackend


class SDBStateManager(StateManager):
    def __init__(self, region, domain_name, schema_class=StateRecord):
        self.region = region
        self.domain_name = domain_name

        super(SDBStateManager, self).__init__(schema_class)

    @property
    def conn(self):
        return self.backend.conn

    @property
    def domain(self):
        return self.backend.domain

    def get_backend(self):
        return SimpleDBBackend(self.region, self.domain_name)

    def save_state(self, task_id, result, previous):
        new_state = self.build_new_state(task_id, result, previous)
        expected_value = ['last_update', False]
        if previous:
            expected_value = ['last_update', previous.last_update.isoformat()]
            if previous.last_update > new_state.last_update:
                logger.warning(task_id + " - found previous state that is "
                               "newer than current state.  Discarding.")
                logger.warning(task_id + " - previous state: %s",
                               previous.to_primitive())
                logger.warning(task_id + " - current state: %s",
                               new_state.to_primitive())
                raise OutOfDateState(new_state, previous)
        logger.debug(task_id + " - saving state: %s",
                     new_state.to_primitive())
        try:
            self.domain.put_attributes(task_id, new_state.to_primitive(),
                                       replace=True,
                                       expected_value=expected_value)
        except SDBResponseError as e:
            if e.error_code == 'ConditionalCheckFailed':
                logger.warning('last_update for %s was updated, skipping',
                               task_id)
                return
            raise

    def get_old_states(self):
        query = ("select * from `%s` where `version` is null or "
                 "`version` < '%s'" % (self.backend.domain_name,
                                       self.schema_class.CURRENT_VERSION))
        return self.domain.select(query, consistent_read=True)
