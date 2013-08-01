import logging

logger = logging.getLogger(__name__)

from nymms.config import config


class LogAlerter(object):
    def __init__(self, *args, **kwargs):
        pass
    
    def alert(self, task_result):
        subject_template = config.settings['alerts']['subject']
        sender = config.settings['alerts']['sender']
        body = config.settings['alerts']['body']
        recipients = config.settings['alerts']['recipients']
        result_data = task_result.serialize()
        logger.debug("Sending SES alert to %s as %s for %s" % (
            recipients, sender, task_result.task['_id']))
