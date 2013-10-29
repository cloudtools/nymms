import unittest

from nymms.utils import templates


class TestNymmsTemplate(unittest.TestCase):
    def test_render_missing(self):
        s = "{{ found_key }} {{ missing_key }}"
        expected = "FOUND {{ missing_key }}"
        context = {'found_key': 'FOUND'}
        t = templates.NymmsTemplate(s)
        self.assertEqual(t.render(context), expected)
