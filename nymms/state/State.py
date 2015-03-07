import logging

logger = logging.getLogger(__name__)

from nymms.schemas import StateRecord, types


class StateManager(object):
    def __init__(self):
        self._backend = None
        self.migrate()
        logger.debug("%s initialized.", self.__class__.__name__)

    @property
    def backend(self):
        if not self._backend:
            self._backend = self.get_backend()
        return self._backend

    def get_backend(self, *args, **kwargs):
        raise NotImplementedError

    def build_new_state(self, task_id, result, previous):
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

    def get_state(self, task_id):
        return self.backend.get(task_id)

    def delete_record(self, record):
        return self.backend.purge(record)

    def filter(self, *args, **kwargs):
        return self.backend.filter(*args, **kwargs)

    def web_filter(self, *args, **kwargs):
        return self.backend.web_filter(*args, **kwargs)

    def migrate(self):
        """ Temporary method, used to update all expressions to the new format
        using schematics & arrow.
        """
        for item in self.get_old_states():
            new_state = StateRecord.migrate(item)
            old_key = item['id']
            self.backend.purge(old_key)
            if new_state:
                logger.debug("Migrating old state %s.", old_key)
                self.backend.put(new_state)
