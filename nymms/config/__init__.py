import imp
import os
import logging

logger = logging.getLogger(__name__)

from nymms.exceptions import NymmsException

class FileNotFound(NymmsException):
    def __init__(self, filename):
        self.filename = filename

    def __str__(self):
        return "Config file '%s' not found." % (self.filename)


config_path = os.path.expanduser(os.environ.get('NYMMS_CONFIG',
        '/etc/nymms/nymms'))

path, module = os.path.split(config_path)

if module.endswith('.py'):
    module = module[:-3]

try:
    module_info = imp.find_module(module, [path])
except ImportError:
    raise FileNotFound(config_path)

logger.debug("Loading config from path: %s" % (config_path))
settings = imp.load_module('settings', *module_info)
