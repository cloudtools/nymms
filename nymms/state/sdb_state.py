import logging

logger = logging.getLogger(__name__)

from nymms import results
from nymms.exceptions import OutOfDateState


class SDBStateBackend(object):
    def __init__(self, conn, domain_name):
        self._conn = conn
        self._domain_name = domain_name
        self._domain = None
        logger.debug("%s initialized.", self.__class__.__name__)

    def _setup_domain(self):
        if self._domain:
            return
        conn = self._conn
        logger.debug("setting up state domain %s", self._domain_name)
        self._domain = conn.create_domain(self._domain_name)

    def _build_new_state(self, task_id, result, previous):
        new_state = results.StateRecord(task_id,
                                        state=result.state,
                                        state_type=result.state_type)
        # Only update last_state_change if the state has changed to a new
        # HARD state_type state, otherwise we use the previous
        # last_state_change
        if previous:
            if (new_state.state_type == results.SOFT or
                    previous.state == new_state.state):
                new_state.last_state_change = previous.last_state_change

        new_state.validate()
        return new_state

    def save_state(self, task_id, result, previous):
        self._setup_domain()
        new_state = self._build_new_state(task_id, result, previous)
        expected_value = ['last_update', False]
        if previous:
            expected_value = ['last_update', previous.last_update]
            if previous.last_update > new_state.last_update:
                logger.warning(task_id + " - found previous state that is "
                               "newer than current state.  Discarding.")
                logger.warning(task_id + " - previous state: %s",
                               previous.serialize())
                logger.warning(task_id + " - current state: %s",
                               new_state.serialize())
                raise OutOfDateState(new_state, previous)
        logger.debug(task_id + " - saving state: %s", new_state.serialize())
        self._domain.put_attributes(task_id, new_state.serialize(),
                                    replace=True,
                                    expected_value=expected_value)

    def get_state(self, task_id):
        self._setup_domain()
        logger.debug("%s - getting state", task_id)
        state_item = self._domain.get_item(task_id, consistent_read=True)
        state = None
        if state_item:
            state = results.StateRecord.deserialize(state_item)
            state.validate()
        else:
            logger.debug("%s - no state found", task_id)
        return state
