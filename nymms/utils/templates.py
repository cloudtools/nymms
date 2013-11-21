from jinja2 import Undefined


class SimpleUndefined(Undefined):
    """ A version of undefined that doesn't freak out when a context
    variable is missing and gives non-verbose help.  Unfortunately it's all
    but impossible with jinja to return the name of a dictionary that is
    missing a key.  We'll make do for now.
    """
    __slots__ = ()

    def __unicode__(self):
        return u'{{!%s}}' % self._undefined_name
