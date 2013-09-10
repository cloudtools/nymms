class NymmsException(Exception):
    """ NYMMS base exception class.
    """
    pass


class OutOfDateState(NymmsException):
    def __init__(self, current, previous):
        self.current_state = current
        self.previous_state = previous

    def __str__(self):
        return "Previous (%d) state newer than current (%d)." % (
            self.previous_state.last_update, self.current_state.last_update)
