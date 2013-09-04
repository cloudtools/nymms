import logging

logger = logging.getLogger(__name__)

from nymms.config import config


class LogAlerter(object):
    def __init__(self, *args, **kwargs):
        pass

    def alert(self, task_result):
        sender = config.settings['alerts']['sender']
        recipients = config.settings['alerts']['recipients']
        task_result.validate()
        logger.debug("Sending SES alert to %s as %s for %s" % (
            recipients, sender, task_result.id))
