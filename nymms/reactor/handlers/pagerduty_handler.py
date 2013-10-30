import logging

logger = logging.getLogger(__name__)

from nymms.reactor.handlers.Handler import Handler
from nymms import results

from jinja2 import Template

try:
    import pagerduty
except ImportError:
    logger.error("Unable to import the pagerduty module.")
    logger.error("Please install it from here: ")
    logger.error("  https://pypi.python.org/pypi/pagerduty/")
    logger.error("(You can use pip, ie: pip install pagerduty)")
    raise


MISSING_SUBJECT = 'Handler %s missing subject_template.'


class PagerDutyHandler(Handler):
    """ A basic handler to send alerts to people via email through Amazon's
    SES service.  Sends every result it receives by default.  To filter
    results you should subclass this and provide a _filter method.

    config options:
      enabled: bool
      subject_template: string, jinja2 Template string
      service_keys: list(string), pagerduty service keys
      filters: list(string), filters
    """
    def _connect(self):
        if getattr(self, '_endpoints', None):
            return
        self._endpoints = []
        service_keys = self.config.get('service_keys', [])
        if not service_keys:
            logger.warning("No service_keys configured for Handler %s.",
                           self.__class__.__name__)
            return
        for key in service_keys:
            logger.debug("Initializing pagerduty service endpoint %s.",
                         key)
            self._endpoints.append(pagerduty.PagerDuty(key))

    def _send_incident(self, result, previous_state):
        self._connect()
        subject_template = self.config.get('subject_template',
           MISSING_SUBJECT % (self.__class__.__name__))
        description = Template(subject_template)
        result_data = result.serialize()
        for ep in self._endpoints:
            logger.debug("Submitting to pagerduty service_key %s.",
                         ep.service_key)
            ep.trigger(description=description.render(result_data),
                       incident_key=result.id,
                       details=result_data)

    def process(self, result, previous_state):
        self._send_incident(result, previous_state)
