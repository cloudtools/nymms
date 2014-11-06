import logging

from nymms.reactor.handlers.Handler import Handler
from nymms.utils.aws_helper import ConnectionManager

from jinja2 import Template
from nymms.utils.templates import SimpleUndefined

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
    @property
    def aws_conn(self):
        if not getattr(self, '_aws_conn', None):
            self._aws_conn = ConnectionManager(region=self.config['region'])
        return self._aws_conn

    def _send_email(self, result, previous_state):
        subject = Template(self.config['subject_template'])
        subject.environment.undefined = SimpleUndefined
        body = Template(self.config['body_template'])
        body.environment.undefined = SimpleUndefined
        sender = self.config['sender']
        recipients = self.config.get('recipients', [])
        result_data = result.serialize()
        if recipients:
            logger.debug("Sending SES alert to %s as %s for %s.",
                         recipients, sender, result.id)
            self.aws_conn.ses.send_email(
                source=sender,
                subject=subject.render(result_data),
                body=body.render(result_data),
                to_addresses=recipients)
        else:
            logger.debug("No valid recipients found, not sending email for "
                         "%s.", result.id)

    def _process(self, result, previous_state):
        self._send_email(result, previous_state)
