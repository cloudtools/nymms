import unittest
import os

os.environ['PATH'] += ":/bin:/usr/bin:/sbin:/usr/sbin:/usr/local/bin"
os.environ['PATH'] += ":/usr/local/sbin"

from nymms.probe.Probe import Probe, TIMEOUT_OUTPUT
from nymms.schemas import types, Result, Task, StateRecord
from nymms import resources
from nymms.state.State import StateManager

import arrow

result_codes = [
    types.STATE_CRITICAL,
    types.STATE_WARNING,
    types.STATE_CRITICAL,
    types.STATE_WARNING,
    types.STATE_WARNING,
    types.STATE_OK,
    types.STATE_OK,
    types.STATE_UNKNOWN,
    types.STATE_OK,
    types.STATE_OK
]

true_output = "Good output"
true_command = resources.Command('true_command', 'echo ' + true_output)
fail_command = resources.Command('fail_command', 'false')
sleep_command = resources.Command('sleep_command', 'sleep {{sleep_time}}')

true_monitor = resources.Monitor('true_monitor', command=true_command)
fail_monitor = resources.Monitor('fail_monitor', command=fail_command)
sleep_monitor = resources.Monitor('sleep_monitor', command=sleep_command)


class DummyStateBackend(object):
    def __init__(self):
        self.states = [
            None,
            {'last_update': 1, 'last_state_change': 0,
                'state': types.STATE_CRITICAL,
                'state_type': types.STATE_TYPE_SOFT},
            {'last_update': 2, 'last_state_change': 0,
                'state': types.STATE_WARNING,
                'state_type': types.STATE_TYPE_SOFT},
            {'last_update': 3, 'last_state_change': 3,
                'state': types.STATE_CRITICAL,
                'state_type': types.STATE_TYPE_HARD},
            {'last_update': 4, 'last_state_change': 4,
                'state': types.STATE_WARNING,
                'state_type': types.STATE_TYPE_HARD},
            {'last_update': 5, 'last_state_change': 4,
                'state': types.STATE_WARNING,
                'state_type': types.STATE_TYPE_HARD},
            {'last_update': 6, 'last_state_change': 6,
                'state': types.STATE_OK, 'state_type': types.STATE_TYPE_HARD},
            {'last_update': 7, 'last_state_change': 6,
                'state': types.STATE_OK, 'state_type': types.STATE_TYPE_HARD},
            {'last_update': 8, 'last_state_change': 8,
                'state': types.STATE_UNKNOWN,
                'state_type': types.STATE_TYPE_SOFT},
            {'last_update': 9, 'last_state_change': 9,
                'state': types.STATE_OK, 'state_type': types.STATE_TYPE_SOFT},
            {'last_update': 10, 'last_state_change': 9,
                'state': types.STATE_OK, 'state_type': types.STATE_TYPE_HARD}
        ]
        self.state_iter = iter(self.states)

    def get(self, item_id, consistent_read=True):
        item = next(self.state_iter)
        if item:
            item['id'] = item_id
        return item


class DummyStateManager(StateManager):
    def __init__(self):
        self._backend = DummyStateBackend()
        self.schema_class = StateRecord


class DummyProbe(Probe):
    def __init__(self, state_manager=DummyStateManager):
        self.task = Task({
            'id': 'test:task',
            'context': {'monitor': {'name': 'true_monitor'}}})
        self.state_manager = state_manager()
        self.results_iter = iter(self.state_manager.backend.states[1:])

    def get_task(self, **kwargs):
        return self.task

    def resubmit_task(self, task, delay, **kwargs):
        self.task.increment_attempt()

    def submit_result(self, result, **kwargs):
        if result.state_type == types.STATE_TYPE_HARD:
            self.task.attempt = 0
        return result

    def execute_task(self, task, timeout, **kwargs):
        result = Result({'id': task.id,
                         'timestamp': task.created,
                         'task_context': task.context})
        r = next(self.results_iter)
        result.state = r['state']
        result.state_type = r['state_type']
        result.output = 'Some output here.'
        result.validate()
        return result


class TestStateChange(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.state_manager = DummyStateManager()
        cls.probe = DummyProbe()
        cls.probe.state_manager = cls.state_manager

    def test_state_change(self):
        # tests that our logic follows the nagios logic here
        # http://nagios.sourceforge.net/docs/3_0/statetypes.html
        # We take our example state changes from the table at the bottom
        t = self.probe.get_task()
        for i, code in enumerate(result_codes):
            r = self.probe.handle_task(t, monitor_timeout=30,
                                       max_retries=2)
            expected = self.state_manager.backend.states[i + 1]
            print "[%d] Result STATE/TYPE: %s/%s" % (i, r.state, r.state_type)
            print "[%d] Expected STATE/TYPE: %s/%s" % (i, expected['state'],
                                                       expected['state_type'])
            self.assertEqual(r.state, expected['state'])
            self.assertEqual(r.state_type, expected['state_type'])
            self.probe.submit_result(r)

    def test_expiration(self):
        expiration = 30
        now = arrow.get()
        t = self.probe.get_task()
        t.created = now
        t.validate()
        self.assertFalse(self.probe.expire_task(t, expiration))
        t.created = now.replace(seconds=-(expiration + 5))
        t.validate()
        self.assertTrue(self.probe.expire_task(t, expiration))


class TestExecuteTask(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.probe = Probe()
        cls.true_task = Task({
            'id': 'test:true_monitor',
            'context': {'monitor': {'name': 'true_monitor'}}})
        cls.fail_task = Task({
            'id': 'test:fail_monitor',
            'context': {'monitor': {'name': 'fail_monitor'}}})
        cls.timeout_task = Task({
            'id': 'test:timeout_monitor',
            'context': {'monitor': {'name': 'sleep_monitor'},
                        'sleep_time': 2}})
        cls.probe._private_context = {}

    def test_successful_execute_task(self):
        result = self.probe.execute_task(self.true_task, 30)
        self.assertEqual(result.state, types.STATE_OK)
        self.assertEqual(result.output.strip(), true_output)

    def test_failed_execute_task(self):
        result = self.probe.execute_task(self.fail_task, 30)
        self.assertEqual(result.state, types.STATE_WARNING)
        self.assertEqual(result.output.strip(), '')

    def test_timeout_execute_task(self):
        timeout = 1
        result = self.probe.execute_task(self.timeout_task, timeout)
        self.assertEqual(result.state, types.STATE_UNKNOWN)
        self.assertEqual(result.output.strip(), TIMEOUT_OUTPUT % timeout)
