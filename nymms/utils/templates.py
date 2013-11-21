from jinja2 import Undefined


class SimpleUndefined(Undefined):
    """ A version of undefined that doesn't freak out when a context
    variable is missing and gives non-verbose help.  Unfortunately it's all
    but impossible with jinja to return the name of a dictionary that is
    missing a key.  We'll make do for now.

    This is a weak hack - I really need to find a way to provide more
    'context' about what is missing in the context.
    """
    __slots__ = ()

    def __unicode__(self):
        return u'{{MISSING_CONTEXT}}'
    def __getattr__(self, attr):
        return u'{{MISSING_CONTEXT}}'
    def __getitem__(self, item):
        return u'{{MISSING_CONTEXT}}'
