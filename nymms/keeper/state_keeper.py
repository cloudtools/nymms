import logging
import json

logger = logging.getLogger(__name__)

from boto.exception import SDBResponseError
from boto.sqs.message import RawMessage

from nymms.config import config
from nymms import results


class StateKeeper(object):
    def __init__(self, conn_mgr):
        self.conn_mgr = conn_mgr
        self.topic_name = config.settings['results_topic']
        self.queue_name = config.settings['states']['queue_name']
        self.domain_name = config.settings['states']['domain']
        self.create_channel()

    def create_channel(self):
        logger.debug("Create SDB domain '%s' for storing state.",
                     self.domain_name)
        self.domain = self.conn_mgr.sdb.create_domain(self.domain_name)
        logger.debug("Creating topic '%s'.", self.topic_name)
        self.topic = self.conn_mgr.sns.create_topic(self.topic_name)
        logger.debug("Creating queue '%s'.", self.queue_name)
        self.queue = self.conn_mgr.sqs.create_queue(self.queue_name)
        self.queue.set_message_class(RawMessage)
        self.topic_arn = self.topic['CreateTopicResponse'][
            'CreateTopicResult']['TopicArn']
        logger.debug("Subscribing queue '%s' to topic '%s'.", self.queue_name,
                     self.topic_name)
        return self.conn_mgr.sns.subscribe_sqs_queue(self.topic_arn,
                                                     self.queue)

    def record(self, task_result):
        log_prefix = "state %s " % (task_result.id,)
        max_attempts = 3
        attempt = 0
        task_id = task_result.id
        result_ts = task_result.timestamp
        while True:
            attempt += 1
            if attempt > max_attempts:
                logger.warning(log_prefix + 'Max attempts reached, dropping '
                               'state record.')
                break
            logger.debug(log_prefix + "getting previous state.")
            previous_state_data = self.domain.get_item(task_id,
                                                       consistent_read=True)
            previous_state = None
            if previous_state_data:
                previous_state = results.StateRecord.deserialize(
                    previous_state_data)
            state_record = results.StateRecord(
                task_result.id,
                state=task_result.state,
                state_type=task_result.state_type,
                timestamp=result_ts)

            # By default we ensure that there is no timestamp for a given
            # record.  This is a sort of janky way to make sure that between
            # when we check to see if a record exists and when we update it
            # that noone creates a record.
            expected_value = ['timestamp', False]
            if previous_state:
                previous_ts = previous_state.timestamp
                expected_value = ['timestamp', previous_ts]
                if int(previous_ts) > result_ts:
                    logger.warning(log_prefix + "Found previous state that is "
                                   "newer than the current state. Discarding.")
                    logger.warning(log_prefix + "previous state: %s",
                                   previous_state.serialize())
                    logger.warning(log_prefix + "new state: %s",
                                   state_record.serialize())
                    return
                # If there is a previous state, and the state is HARD AND
                # the previous state and current state are the same then just
                # update the timestamp
                # This prevents flapping of state
                if previous_state.state == task_result.state:
                    logger.debug
                    if previous_state.state_type == results.HARD:
                        logger.warning(log_prefix + "HARD state has not "
                                       "changed.  Only updating timestamp.")
                        state_record = previous_state
                        state_record.timestamp = result_ts

            try:
                logger.debug(log_prefix + "Updating state: %s",
                             state_record.serialize())
                self.domain.put_attributes(task_id,
                                           state_record.serialize(),
                                           replace=True,
                                           expected_value=expected_value)
                break
            except SDBResponseError, e:
                if e.status == 409:
                    # Conditional check failed
                    logger.warning(log_prefix + "State updated by someone "
                                   "else.  Retrying.")
                    continue

    def get_result(self):
        if not getattr(self, 'queue', None):
            logger.debug('Not attached to queue. Attaching.')
            self.create_channel()
        wait_time = config.settings['states']['queue_wait_time']
        timeout = config.settings['states']['visibility_timeout']
        logger.debug("Getting result from queue '%s'.", self.queue_name)
        result = self.queue.read(visibility_timeout=timeout,
                                 wait_time_seconds=wait_time)
        result_object = None
        if result:
            result_message = json.loads(result.get_body())['Message']
            result_dict = json.loads(result_message)
            result_object = results.Result.deserialize(result_dict,
                                                       origin=result)
            result_object.validate()
        return result_object

    def run(self):
        while True:
            task_result = self.get_result()
            if not task_result:
                logger.debug("Result queue '%s' is empty.", self.queue_name)
                continue
            self.record(task_result)
            task_result.delete()
