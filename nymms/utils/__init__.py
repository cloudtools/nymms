import logging
import time
import importlib
import sys
import collections

import arrow

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
    """ Parses timestamps and returns an arrow time object.

    Takes a time_string in either ISO-8601 format, a unix timestamp,
    or a time offset in the form of [+-]XXXX[smhd] and returns an arrow time
    object with at that time.

    Can take an optional reference_time arrow object, which will only be
    used in the case that an offset was given, and will be used in place of
    now for offsets.
    """
    suffix_map = {'s': 'seconds',
                  'm': 'minutes',
                  'h': 'hours',
                  'd': 'days'}
    if time_string[0] in ('+', '-'):
        unit = 's'
        offset = time_string
        if time_string[-1] in ('s', 'm', 'h', 'd'):
            unit = time_string[-1]
            offset = offset[:-1]
        result_time = arrow.get(reference_time)
        replace_args = {suffix_map[unit]: int(offset)}
        result_time = result_time.replace(**replace_args)
    elif '-' in time_string:
        result_time = arrow.get(time_string)
    else:
        raise ValueError(time_string)
    return result_time
