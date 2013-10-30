from jinja2 import Template, StrictUndefined


class NymmsTemplate(Template):
    """ Throws exceptions for missing context values. """
    def __new__(cls, *args, **kwargs):
        kwargs['undefined'] = StrictUndefined
        return super(NymmsTemplate, cls).__new__(cls, *args, **kwargs)
