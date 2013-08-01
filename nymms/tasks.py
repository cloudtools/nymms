import logging
import time

logger = logging.getLogger(__name__)


class Task(dict):
    id_format = "{node[name]}:{monitor[name]}"

    def __init__(self, *args, **kwargs):
        ret = dict.__init__(self, *args, **kwargs)
        if not '_id' in self:
            self['_id'] = self.create_id()
        if not '_attempt' in self:
            self['_attempt'] = 0
        if not '_created' in self:
            self['_created'] = time.time()
        if not '_instance' in self:
            self['_instance'] = self.create_instance()
        return ret

    def create_id(self):
        return self.id_format.format(**self)

    def create_instance(self):
        return self['_id'] + ":%f" % (self['_created'],)

    @property
    def id(self):
        return self['_id']

    @property
    def instance(self):
        return self['_instance']
