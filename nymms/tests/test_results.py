import unittest
import copy

from nymms import results

result_data = {
    'task_url': 'nymms://db1/check_postgres/?timestamp=111111.111',
    'status': 0,
    'state': 0,
    'data': {'key': 'test data'},
}

class TestTaskResult(unittest.TestCase):
    def setUp(self):
        self.data = copy.deepcopy(result_data)

    def test_invalid_state_name(self):
        self.data['state'] = 'foo'
        with self.assertRaises(result.InvalidState):
            result.TaskResult(**self.data)

    def test_invalid_status_name(self):
        self.data['status'] = 'foo'
        with self.assertRaises(result.InvalidStatus):
            result.TaskResult(**self.data)

    def test_set_bad_status(self):
        local_result = result.TaskResult(**self.data)
        with self.assertRaises(result.InvalidStatus):
            local_result.status = 'foo'

    def test_set_bad_state(self):
        local_result = result.TaskResult(**self.data)
        with self.assertRaises(result.InvalidState):
            local_result.state = 'foo'

    def test_state_name(self):
        local_result = result.TaskResult(**self.data)
        self.assertEqual(local_result.state_name,
            result.states[result_data['state']])

    def test_status_name(self):
        local_result = result.TaskResult(**self.data)
        self.assertEqual(local_result.status_name,
            result.statuses[result_data['status']])

    def test_serialize(self):
        local_result = result.TaskResult(**self.data)
        self.assertEqual(local_result.serialize(), result_data)
