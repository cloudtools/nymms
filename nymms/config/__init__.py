import imp
import os
import logging

logger = logging.getLogger(__name__)

from nymms.exceptions import NymmsException

DEFAULTS = {}

class FileNotFound(NymmsException):
    def __init__(self, filename):
        self.filename = filename

    def __str__(self):
        return "Config file '%s' not found." % (self.filename)


class SettingNotFound(NymmsException):
    def __init__(self, setting_name):
        self.setting_name = setting_name

    def __str__(self):
        return "Setting '%s' not found." % (self.setting_name)


config_path = os.path.expanduser(os.environ.get('NYMMS_CONFIG',
        '/etc/nymms/nymms'))


class DefaultSettingsProxy(object):
    def __init__(self, config_path=config_path, defaults=None):
        self.config_path = config_path
        self.settings = None
        if not defaults:
            self.defaults = {}
        else:
            self.defaults = defaults

        self._load_config()

    def _load_config(self, force=False):
        if self.settings and not force:
            logger.debug('Settings already loaded and force=False. Skipping '
                    'reload.')
            return
        path, module = os.path.split(config_path)
        if module.endswith('.py'):
            module = module[:-3]

        try:
            module_info = imp.find_module(module, [path])
        except ImportError:
            raise FileNotFound(config_path)

        logger.debug("Loading config from path: %s" % (config_path))
        self.settings = imp.load_module('settings', *module_info)

    def __getattr__(self, attr):
        """ First check the settings module, then the defaults dictionary.

        If neither of those have the setting, raise SettingNotFound.
        """
        try:
            try:
                value = getattr(self.settings, attr)
                logger.debug('Setting found in settings file.')
            except AttributeError:
                value = self.defaults[attr]
                logger.debug("Setting '%s' found in defaults." % (attr))
        except KeyError:
            logger.error("Setting '%s' not found." % (attr))
            raise SettingNotFound(attr)
        return value

settings = DefaultSettingsProxy(config_path, defaults=DEFAULTS)
