import logging
import time
import importlib
import sys
import collections

from nymms.exceptions import InvalidTimeFormat

logger = logging.getLogger(__name__)


def retry_on_exception(exception_list, retries=3, reset_func=None,
                       final_exception=None, delay=0):
    """ A decorator that executes a function and catches any exceptions in
    'exception_list'.  It then retries 'retries' with 'delay' seconds between
    retries and executing 'reset_func' each time.  If it fails after reaching
    the retry limit it then raises 'final_exception' or the last exception
    raised.
    """
    def decorator(func):
        def wrapped(*args, **kwargs):
            i = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except exception_list as e:
                    if reset_func:
                        reset_func()
                    if delay:
                        if callable(delay):
                            time.sleep(delay(i))
                        else:
                            time.sleep(delay)
                    logger.warn("%s exception caught.  Retrying %d time(s): "
                                "%s", e.__class__.__name__, retries - i,
                                e.message)
                i += 1
                if retries and i > retries:
                    break
            if final_exception:
                raise final_exception(str(e))
            else:
                raise e
        return wrapped
    return decorator


def load_object_from_string(fqcn):
    """ Given a '.' delimited string representing the full path to an object
    (function, class, variable) inside a module, return that object.  Example:

    load_object_from_string('os.path.basename')
    load_object_from_string('logging.Logger')
    load_object_from_string('LocalClassName')
    """
    module_path = '__main__'
    object_name = fqcn
    if '.' in fqcn:
        module_path, object_name = fqcn.rsplit('.', 1)
        importlib.import_module(module_path)
    return getattr(sys.modules[module_path], object_name)


def deep_update(orig, upd):
    """ Does a 'deep' update of dictionary 'orig' with dictionary 'upd'."""
    for k, v in upd.iteritems():
        if isinstance(v, collections.Mapping):
            r = deep_update(orig.get(k, {}), v)
            orig[k] = r
        else:
            orig[k] = upd[k]
    return orig


def parse_time(time_string, reference_time=None):
    """Parses a time in YYYYMMDDHHMMSS or +XXXX[smhd] and returns
    epoch time

    reference_time should be the epoch time used for calculating
    the time when using +XXXX[smhd]

    if time_string == 0, returns None"""
    if time_string == '0':
        return None

    if time_string[0] == '+' or time_string[0] == '-':
        if not reference_time:
            reference_time = int(time.time())

        last_char = time_string[len(time_string) - 1]
        user_value = time_string[0:(len(time_string) - 1)]
        if last_char == 's':
            epoch = reference_time + int(user_value)
        elif last_char == 'm':
            epoch = reference_time + (int(user_value) * 60)
        elif last_char == 'h':
            epoch = reference_time + (int(user_value) * 60 * 60)
        elif last_char == 'd':
            epoch = reference_time + (int(user_value) * 60 * 60 * 24)
        else:
            raise InvalidTimeFormat(time_string)
    else:
        epoch = int(time.strftime("%s",
                    time.strptime(time_string, "%Y%m%d%H%M%S")))

    return epoch
