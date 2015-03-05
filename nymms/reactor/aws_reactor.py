import logging
import json

logger = logging.getLogger(__name__)

from nymms.reactor.Reactor import Reactor
from nymms.suppress.sdb_suppress import SDBSuppressFilterBackend
from nymms.utils.aws_helper import SNSTopic, ConnectionManager
from nymms.state.sdb_state import SDBStateBackend
from nymms.schemas import Result

from boto.sqs.message import RawMessage


class AWSReactor(Reactor):
    def __init__(self, region, topic_name, state_domain_name, queue_name,
                 suppress_domain_name, suppress_cache_timeout=60,
                 state_backend=SDBStateBackend,
                 suppress_backend=SDBSuppressFilterBackend):
        super(AWSReactor, self).__init__()
        self.region = region
        self.topic_name = topic_name
        self.queue_name = queue_name

        self._conn = None
        self._queue = None

        self.state_backend = state_backend(region, state_domain_name)
        self.suppress_backend = suppress_backend(region,
                                                 suppress_cache_timeout,
                                                 suppress_domain_name)

    @property
    def conn(self):
        if not self._conn:
            self._conn = ConnectionManager(self.region)
        return self._conn

    @property
    def queue(self):
        if not self._queue:
            self._queue = self.conn.sqs.create_queue(self.queue_name)
            self._queue.set_message_class(RawMessage)
            topic = SNSTopic(self.region, self.topic_name)
            topic.subscribe_sqs_queue(self.queue)
        return self._queue

    def get_result(self, **kwargs):
        wait_time = kwargs.get('wait_time', 0)
        visibility_timeout = kwargs.get('visibility_timeout', None)

        logger.debug("Getting result from queue %s.", self.queue_name)
        result = self.queue.read(visibility_timeout=visibility_timeout,
                                 wait_time_seconds=wait_time)
        result_obj = None
        if result:
            result_message = json.loads(result.get_body())['Message']
            result_dict = json.loads(result_message)
            # Not sure why these fields are sometimes serialized but
            # mostly not... regardless they cause problems because they
            # are just properties of the model and not fields.
            result_dict.pop('state_name', None)
            result_dict.pop('state_type_name', None)
            try:
                result_obj = Result(result_dict, origin=result)
                result_obj.validate()
            except Exception as e:
                logger.debug('Got unexpected message: %s', result_dict)
                logger.exception(
                    'Error reading result from queue: %s', e.message)
        return result_obj

    def delete_result(self, result):
        self.queue.delete_message(result._origin)
