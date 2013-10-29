from jinja2 import Template, Undefined


class IgnoreUndefined(Undefined):
    """ Ignores Undefined values in the context. """
    def __unicode__(self):
        return u'{{ %s }}' % self._undefined_name


class NymmsTemplate(Template):
    """ Uses the IgnoreUndefined class for undefined values. """
    def __new__(cls, *args, **kwargs):
        kwargs['undefined'] = IgnoreUndefined
        return super(NymmsTemplate, cls).__new__(cls, *args, **kwargs)
