import json
import base64
import logging

logger = logging.getLogger(__name__)


class NanoMessage(object):
    def __init__(self, message):
        self.original = message
        self.attributes = message.attributes
        self.data = json.loads(message.get_body())
        self.task = json.loads(base64.b64decode(self.data['Message']))

    def delete(self):
        return self.original.delete()
