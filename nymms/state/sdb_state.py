import logging

logger = logging.getLogger(__name__)

from boto.exception import SDBResponseError

from nymms.state.State import StateBackend
from nymms.schemas import StateRecord, types
from nymms.exceptions import OutOfDateState
from nymms.utils import aws_helper


class SDBStateBackend(StateBackend):
    def __init__(self, region, domain_name):
        self.region = region
        self.domain_name = domain_name

        self._conn = None
        self._domain = None
        super(SDBStateBackend, self).__init__()

    @property
    def conn(self):
        if not self._conn:
            self._conn = aws_helper.ConnectionManager(self.region).sdb
        return self._conn

    @property
    def domain(self):
        if not self._domain:
            self._domain = self.conn.create_domain(self.domain_name)
        return self._domain

    def _build_new_state(self, task_id, result, previous):
        new_state = StateRecord({'id': task_id,
                                 'state': result.state,
                                 'state_type': result.state_type})
        # Only update last_state_change if the state has changed to a new
        # HARD state_type state, otherwise we use the previous
        # last_state_change
        if previous:
            if (new_state.state_type is types.STATE_TYPE_SOFT or
                    previous.state is new_state.state):
                new_state.last_state_change = previous.last_state_change

        new_state.validate()
        return new_state

    def save_state(self, task_id, result, previous):
        new_state = self._build_new_state(task_id, result, previous)
        expected_value = ['last_update', False]
        if previous:
            expected_value = ['last_update', previous.last_update.timestamp]
            if previous.last_update > new_state.last_update:
                logger.warning(task_id + " - found previous state that is "
                               "newer than current state.  Discarding.")
                logger.warning(task_id + " - previous state: %s",
                               previous.serialize())
                logger.warning(task_id + " - current state: %s",
                               new_state.serialize())
                raise OutOfDateState(new_state, previous)
        logger.debug(task_id + " - saving state: %s", new_state.serialize())
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

    def get_state(self, task_id):
        logger.debug("%s - getting state", task_id)
        state_item = self.domain.get_item(task_id, consistent_read=True)
        state = None
        if state_item:
            state = self.deserialize_state(state_item)
        else:
            logger.debug("%s - no state found", task_id)
        return state

    def get_all_states(self, filters=None, order_by='last_update',
                       model_cls=StateRecord):
        query = "select * from %s" % (self.domain_name)
        if filters:
            query += " where "
        query += ' and '.join(filters)

        if order_by:
            query += " where %s is not null" % order_by
            query += " order by `%s`" % order_by

        states = []
        for item in self.domain.select(query):
            states.append(self.deserialize_state(item, model_cls=model_cls))
        return states

    def delete_record(self, record):
        record._origin.delete()
