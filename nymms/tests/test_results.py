import unittest
import copy

from nymms import results

result_data = {
    'result_id': 'www1:check_http',
    'status': results.OK,
    'state': results.SOFT,
    'task_context': {'key': 'test data'},
}

class TestResult(unittest.TestCase):
    def setUp(self):
        self.data = copy.deepcopy(result_data)

    def test_invalid_state_name(self):
        self.data['state'] = 'foo'
        with self.assertRaises(results.ResultValidationError):
            results.Result(**self.data)

    def test_invalid_status_name(self):
        self.data['status'] = 'foo'
        with self.assertRaises(results.ResultValidationError):
            results.Result(**self.data)

    def test_set_bad_status(self):
        local_result = results.Result(**self.data)
        with self.assertRaises(results.ResultValidationError):
            local_result.status = 'foo'

    def test_set_bad_state(self):
        local_result = results.Result(**self.data)
        with self.assertRaises(results.ResultValidationError):
            local_result.state = 'foo'

    def test_state_name(self):
        local_result = results.Result(**self.data)
        self.assertEqual(local_result.state_name,
            results.states[result_data['state']])

    def test_status_name(self):
        local_result = results.Result(**self.data)
        self.assertEqual(local_result.status_name,
            results.statuses[result_data['status']])

    def test_serialize(self):
        local_result = results.Result(**self.data)
        for k, v in result_data.items():
            self.assertEqual(v, getattr(local_result, k))
