import logging

logger = logging.getLogger(__name__)

from nymms.schemas import StateRecord, types


class StateManager(object):
    def __init__(self, schema_class=StateRecord):
        self._backend = None
        self.schema_class = schema_class
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
        new_state = self.schema_class({'id': task_id,
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

    def deserialize(self, item, strict=False):
        try:
            item_obj = self.schema_class(item, strict=strict, origin=item)
            item_obj.validate()
            return item_obj
        except Exception:
            logger.exception("Problem deserializing item:")
            logger.error("Data: %s", str(item))
            return None

    def get_state(self, task_id):
        item = self.backend.get(task_id)
        if item:
            return self.deserialize(item)
        return None

    def delete_record(self, record):
        return self.backend.purge(record)

    def filter(self, *args, **kwargs):
        result, next_token = self.backend.filter(*args, **kwargs)
        return ([self.deserialize(i) for i in result], next_token)

    def migrate(self):
        """ Temporary method, used to update all expressions to the new format
        using schematics & arrow.
        """
        for item in self.get_old_states():
            new_state = self.schema_class.migrate(item)
            old_key = item['id']
            self.backend.purge(old_key)
            if new_state:
                logger.debug("Migrating old state %s.", old_key)
                self.backend.put(new_state)
