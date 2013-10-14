import logging

from nymms.reactor.handlers.Handler import Handler
from nymms.utils.aws_helper import ConnectionManager
from nymms import results

from jinja2 import Template

logger = logging.getLogger(__name__)


class SESHandler(Handler):
    """ A basic handler to send alerts to people via email through Amazon's
    SES service.  Sends every result it receives by default.  To filter
    results you should subclass this and provide a _filter method.

    config options:
      enabled: bool
      region: string, aws region (us-east-1, etc)
      sender: string, email address
      subject_template: string
      body_template: string
      recipients: list, email addresses
      filters: list, filters
    """
    def _connect(self):
        if getattr(self, '_aws_conn', None):
            return
        self._aws_conn = ConnectionManager(region=self.config['region'])

    def _send_email(self, result, previous_state):
        self._connect()
        subject = Template(self.config['subject_template'])
        body = Template(self.config['body_template'])
        sender = self.config['sender']
        recipients = self.config['recipients']
        result_data = result.serialize()
        logger.debug("Sending SES alert to %s as %s for %s.",
                     recipients, sender, result.id)
        self._aws_conn.ses.send_email(
            source=sender,
            subject=subject.render(result_data),
            body=body.render(result_data),
            to_addresses=recipients
        )

    def process(self, result, previous_state):
        self._send_email(result, previous_state)
