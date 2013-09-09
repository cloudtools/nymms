import uuid
import logging
import json
import glob
import os
import imp

logger = logging.getLogger(__name__)

from nymms import results
from nymms.reactor.Reactor import Reactor
from nymms.utils.aws_helper import SNSTopic

from boto.sqs.message import RawMessage


class AWSReactor(Reactor):
    def __init__(self, conn_mgr, topic_name, state_domain_name, queue_name):
        self._conn = conn_mgr
        self._topic_name = topic_name
        self._state_domain_name = state_domain_name
        self._queue_name = queue_name
        self._topic = None
        self._queue = None
        self._state_domain = None
        self._handlers = {}
        logger.debug(self.__class__.__name__ + " initialized.")

    def _setup_queue(self):
        if self._queue:
            return
        logger.debug("setting up queue %s", self._queue_name)
        self._queue = self._conn.sqs.create_queue(self._queue_name)
        self._queue.set_message_class(RawMessage)

    def _setup_topic(self):
        if self._topic:
            return
        logger.debug("setting up topic %s", self._topic_name)
        self._topic = SNSTopic(self._conn, self._topic_name)
        logger.debug("subscribing queue %s to topic %s", self._queue_name,
                     self._topic_name)
        self._topic.subscribe_sqs_queue(self._queue)

    def _setup_state_domain(self):
        if self._state_domain:
            return
        conn = self._conn.sdb
        logger.debug("setting up state domain %s", self._state_domain_name)
        self._state_domain = conn.create_domain(self._state_domain_name)

    def get_result(self, wait_time=0, visibility_timeout=None):
        self._setup_queue()
        self._setup_topic()
        logger.debug("Getting result from queue %s.", self._queue_name)
        result = self._queue.read(visibility_timeout=visibility_timeout,
                                  wait_time_seconds=wait_time)
        result_obj = None
        if result:
            result_message = json.loads(result.get_body())['Message']
            result_dict = json.loads(result_message)
            result_obj = results.Result.deserialize(result_dict,
                                                    origin=result)
            result_obj.validate()
        return result_obj

    def get_state(self, task_id):
        self._setup_state_domain()
        state_item = self._state_domain.get_item(task_id,
                                                 consistent_read=True)
        state = None
        if state_item:
            state = results.StateRecord.deserialize(state_item)
        return state

    def run(self, handler_config_path, wait_time, visibility_timeout):
        self._load_handlers(handler_config_path)
        while True:
            result = self.get_result(wait_time, visibility_timeout)
            if not result:
                logger.debug('Result queue empty.')
                continue
            self.handle_result(result)
            result.delete()
