import logging

logger = logging.getLogger(__name__)

from nymms import results


def always_true(result, previous_state):
    """ Not really necessary since no filters results in an always true result,
    but this is useful to show an example of what a filter is without actually
    doing anything.
    """
    return True


def hard_state(result, previous_state):
    if result.state_type == results.HARD:
        logger.debug("%s state_type is HARD.", result.id)
        return True
    return False


def changed_state(result, previous_state):
    """ Only alert if the state is new or has either changed state or
    state_type.
    """
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


def ok_state(result, previous_state):
    if result.state == results.OK:
        return True
    return False


def warning_state(result, previous_state):
    if result.state == results.WARNING:
        return True
    return False


def critical_state(result, previous_state):
    if result.state == results.CRITICAL:
        return True
    return False


def unknown_state(result, previous_state):
    if result.state >= results.UNKNOWN:
        return True
    return False


def not_ok_state(result, previous_state):
    return not(ok_state(result, previous_state))


def passive_command(result, previous_state):
    return result.task_context['command_type'] == 'passive'


def active_command(result, previous_state):
    return not passive_command(result, previous_state)


def not_soft_recovery(result, previous_state):
    if previous_state.state_type == results.SOFT:
        if result.state_type == results.SOFT and result.state == results.OK:
            return False
    return True
