import logging

logger = logging.getLogger(__name__)

from nymms import results


def hard_state(result, previous_state):
    if result.state_type == results.HARD:
        logger.debug("%s state_type is HARD.", result.id)
        return True
    return False


def changed_hard_state(result, previous_state):
    """ Returns true if the current state is a HARD state and either the state
    or state_type has changed since the stored last result.
    """
    if hard_state(result, previous_state):
        logger.debug("%s state_type is HARD.", result.id)
        if not previous_state:
            logger.debug("No previous state found.")
            return True
        if not previous_state.state == result.state:
            logger.debug("Previous state (%s) does not match current "
                         "state (%s).", previous_state.state_name,
                         result.state_name)
            return True
        if not previous_state.state_type == result.state_type:
            logger.debug("Previous state_type (%s) does not match current "
                         "state_type (%s).",
                         previous_state.state_type_name,
                         result.state_type_name)
            return True
    return False
