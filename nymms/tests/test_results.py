import unittest

from nymms import results
from nymms.data_types import ValidationError, MissingRequiredField


class TestResult(unittest.TestCase):
    def setUp(self):
        self.result = results.Result(
            'www1:check_http',
            state=results.OK,
            state_type=results.HARD,
            timestamp=123456,
            output='OK: check_http is ok',
            task_context={'url': 'http://example.com/'})

    def test_invalid_state_name(self):
        self.result.state = 'foo'
        with self.assertRaises(ValidationError):
            self.result.serialize()

    def test_invalid_state_type_name(self):
        self.result.state_type = 'foo'
        with self.assertRaises(ValidationError):
            self.result.validate()

    def test_missing_state(self):
        delattr(self.result, 'state')
        with self.assertRaises(MissingRequiredField):
            self.result.validate()

    def test_serialize_deserialize(self):
        serialize1 = self.result.serialize()
        new_result = results.Result.deserialize(serialize1)
        serialize2 = new_result.serialize()
        self.assertEqual(serialize1, serialize2)
