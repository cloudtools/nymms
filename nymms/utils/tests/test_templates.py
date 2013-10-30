import unittest

from jinja2.exceptions import UndefinedError

from nymms.utils import templates


class TestNymmsTemplate(unittest.TestCase):
    def test_render_missing(self):
        s = "{{ found_key }} {{ missing_key }}"
        context = {'found_key': 'FOUND'}
        with self.assertRaises(UndefinedError):
            t = templates.NymmsTemplate(s)
            t.render(context)
