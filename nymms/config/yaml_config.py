import glob
import os
import logging
import hashlib
import re

logger = logging.getLogger(__name__)

import yaml

from nymms import exceptions

include_regex = re.compile(r'^(?P<indent>\s*)\!include (?P<path>[^\s]+)$')


class EmptyConfig(exceptions.NymmsException):
    def __init__(self, filename):
        self.filename = filename

    def __str__(self):
        return "Config file %s resulted in an empty config." % (self.filename)


def open_config_file(config_file):
    """ Opens a config file, logging common IOError exceptions.
    """
    try:
        return open(config_file)
    except IOError, e:
        # This should only happen with the top level config file, since
        # we use glob.glob on includes
        if e.errno == 2:
            logger.error("Could not find file '%s'.", config_file)
        elif e.errno == 13:
            logger.error("Invalid permissions to open '%s'.", config_file)
        raise


def load_config(config_file):
    stack = []
    root = os.path.dirname(os.path.abspath(os.path.expanduser(config_file)))

    def recursive_preprocess(filename, indent=''):
        filename = os.path.expanduser(filename)
        stack.append(os.path.abspath(filename))
        c = []

        with open_config_file(filename) as fd:
            for lineno, line in enumerate(fd):
                line = line.rstrip()
                match = include_regex.match(line)
                if match:
                    path = match.group('path')
                    indent = indent + match.group('indent')
                    # if the include doesn't have a fully qualified path then
                    # assume the relative path is based off the directory of
                    # the initial config file
                    if not path.startswith('/'):
                        path = os.path.join(root, path)
                    files = glob.glob(path)
                    if not files:
                        logger.warning("Include statement '%s' at %s:%d did "
                                       "not match any files. Skipping.", line,
                                       filename, lineno)
                        continue
                    for f in files:
                        f = os.path.abspath(f)
                        if f in stack:
                            logger.warning("Already parsed %s, skipping "
                                           "(%s:%d) to avoid infinite loop.",
                                           f, filename, lineno)
                            continue
                        if os.path.isfile(f):
                            logger.debug("Parsing include (%s:%d): %s",
                                         filename, lineno, f)
                            c.extend(recursive_preprocess(f, indent))
                        else:
                            logger.warning("%s is not a regular file, "
                                           "skipping (%s:%d).", f, filename,
                                           lineno)
                    continue
                c.append(indent + line)
        return c
    logger.debug("Loading config file: %s", config_file)
    config = recursive_preprocess(config_file)
    if not config:
        raise EmptyConfig(config_file)
    config = os.linesep.join(config)
    version = hashlib.sha512(config).hexdigest()
    return (version, yaml.safe_load(config))
