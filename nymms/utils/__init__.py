import logging
import time
import imp
import sys

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


def load_class_from_name(fqcn):
    """ Returns a class given a dot delimited string defining its path. """
    module_parts = fqcn.split('.')
    class_name = module_parts[-1]
    path_parts = module_parts[:-1]
    current_mod = None
    current_name = None
    for part in path_parts:
        if current_mod:
            current_path = current_mod.__path__
            current_name = '.'.join([current_name, part])
        else:
            current_path = sys.path
            current_name = part
        try:
            current_mod = sys.modules[current_name]
            logger.debug("Module %s already loaded, skipping.", current_name)
        except KeyError:
            args = imp.find_module(part, current_path)
            current_mod = imp.load_module(current_name, *args)
    return getattr(current_mod, class_name)
