import logging

logger = logging.getLogger(__name__)

from nymms.schemas import StateRecord


class StateBackend(object):
    def __init__(self):
        logger.debug("%s initialized.", self.__class__.__name__)

    def deserialize_state(self, item, model_cls=StateRecord):
        try:
            state = model_cls(item, strict=False, origin=item)
            state.validate()
            return state
        except Exception:
            logger.exception("Problem deserializing state:")
            logger.error("State data: %s", str(item))
            return None
