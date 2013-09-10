import logging
import json

logger = logging.getLogger(__name__)

from nymms import results
from nymms.reactor.Reactor import Reactor
from nymms.utils.aws_helper import SNSTopic
from nymms.state.sdb_state import SDBStateBackend

from boto.sqs.message import RawMessage


class AWSReactor(Reactor):
    def __init__(self, conn_mgr, topic_name, state_domain_name, queue_name,
                 state_backend=SDBStateBackend):
        self._conn = conn_mgr
        self._topic_name = topic_name
        self._queue_name = queue_name
        self._topic = None
        self._queue = None
        self._state_backend = state_backend(conn_mgr.sdb, state_domain_name)
        super(AWSReactor, self).__init__()

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

    def get_result(self, **kwargs):
        wait_time = kwargs.get('wait_time', 0)
        visibility_timeout = kwargs.get('visibility_timeout', None)
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
