import unittest

from nymms.probe.Probe import Probe
from nymms import results
from nymms.tasks import Task

result_codes = [
    results.CRITICAL,
    results.WARNING,
    results.CRITICAL,
    results.WARNING,
    results.WARNING,
    results.OK,
    results.OK,
    results.UNKNOWN,
    results.OK,
    results.OK
]


class DummyStateBackend(object):
    def __init__(self):
        self.states = [
            None,
            {'last_update': 1, 'last_state_change': 0,
                'state': results.CRITICAL, 'state_type': results.SOFT},
            {'last_update': 2, 'last_state_change': 0,
                'state': results.WARNING, 'state_type': results.SOFT},
            {'last_update': 3, 'last_state_change': 3,
                'state': results.CRITICAL, 'state_type': results.HARD},
            {'last_update': 4, 'last_state_change': 4,
                'state': results.WARNING, 'state_type': results.HARD},
            {'last_update': 5, 'last_state_change': 4,
                'state': results.WARNING, 'state_type': results.HARD},
            {'last_update': 6, 'last_state_change': 6,
                'state': results.OK, 'state_type': results.HARD},
            {'last_update': 7, 'last_state_change': 6,
                'state': results.OK, 'state_type': results.HARD},
            {'last_update': 8, 'last_state_change': 8,
                'state': results.UNKNOWN, 'state_type': results.SOFT},
            {'last_update': 9, 'last_state_change': 9,
                'state': results.OK, 'state_type': results.SOFT},
            {'last_update': 10, 'last_state_change': 9,
                'state': results.OK, 'state_type': results.HARD}
        ]
        self.state_iter = iter(self.states)

    def get_state(self, task_id):
        state_item = next(self.state_iter)
        state = None
        if state_item:
            state_item['id'] = task_id
            state = results.StateRecord.deserialize(state_item)
            state.validate()
        return state


class DummyProbe(Probe):
    def __init__(self):
        self.task = Task('test:task', context={})
        self.results_iter = iter(result_codes)
        
    def get_task(self, **kwargs):
        return self.task

    def resubmit_task(self, task, delay):
        self.task.increment_attempt()

    def submit_result(self, result):
        if result.state_type == results.HARD:
            self.task.attempt = 0
        return result

    def execute_task(self, task, timeout):
        result = results.Result(task.id, timestamp=task.created,
                                task_context=task.context)
        result.state = next(self.results_iter)
        result.output = 'Some output here.'
        return result


class TestStateChange(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.state_backend = DummyStateBackend()
        cls.probe = DummyProbe()
        cls.probe._state_backend = cls.state_backend

    def test_state_change(self):
        # tests that our logic follows the nagios logic here
        # http://nagios.sourceforge.net/docs/3_0/statetypes.html
        # We take our example state changes from the table at the bottom
        t = self.probe.get_task()
        for i, code in enumerate(result_codes):
            r = self.probe.handle_task(t, monitor_timeout=30,
                                       max_retries=2)
            expected = self.state_backend.states[i + 1]
            print "[%d] Result STATE/TYPE: %s/%s" % (i, r.state, r.state_type)
            print "[%d] Expected STATE/TYPE: %s/%s" % (i, expected['state'],
                                            expected['state_type'])
            self.assertEqual(r.state, expected['state'])
            self.assertEqual(r.state_type, expected['state_type'])
            self.probe.submit_result(r)
