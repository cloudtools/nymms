import boto
import imp

CONNECT_MAP = {
    'beanstalk': ['beanstalk'],
    'cloudformation': ['cloudformation'],
    'cloudsearch': ['cloudsearch'],
    'dynamodb': ['dynamodb'],
    'dynamodb2': ['dynamodb2'],
    'ec2': ['ec2'],
    'autoscale': ['ec2', 'autoscale'],
    'cloudwatch': ['ec2', 'cloudwatch'],
    'elb': ['ec2', 'elb'],
    'elasticache': ['elasticache'],
    'elastictranscoder': ['elastictranscoder'],
    'emr': ['emr'],
    'glacier': ['glacier'],
    'iam': ['iam'],
    'rds': ['rds'],
    'redshift': ['redshift'],
    'route53': ['route53'],
    's3': ['s3'],
    'sdb': ['sdb'],
    'ses': ['ses'],
    'sns': ['sns'],
    'sqs': ['sqs'],
    'sts': ['sts'],
    'support': ['support'],
    'swf': ['swf'],
    'vpc': ['vpc'],
}


class ConnectionManager(object):
    """ Used to setup and maintain AWS service connections in a single region.

    This acts as a proxy for AWS connections to all AWS services that boto
    provides a connect_to_region method for.
    """
    def __init__(self, region='us-east-1', **kw_params):
        self.region = region
        self.params = kw_params

    def __getattr__(self, attr):
        try:
            modules = CONNECT_MAP[attr]
        except KeyError:
            raise AttributeError(attr)

        current_mod = boto
        for m in modules:
            x = imp.find_module(m, current_mod.__path__)
            current_mod = imp.load_module(attr, *x)
        connect_to_region = getattr(current_mod, 'connect_to_region')
        conn = connect_to_region(self.region, **self.params)
        setattr(self, attr, conn)
        return conn


class SNSTopic(object):
    def __init__(self, conn_mgr, topic_name):
        self._conn = conn_mgr.sns
        self._topic_name = topic_name
        self._topic_arn = None

    def _setup_topic(self):
        if self._topic_arn:
            return

        conn = self._conn
        response = conn.create_topic(self._topic_name)['CreateTopicResponse']
        self._topic_arn = response['CreateTopicResult']['TopicArn']

    def publish(self, *args, **kwargs):
        self._setup_topic()
        return self._conn.publish(self._topic_arn, *args, **kwargs)

    def subscribe_sqs_queue(self, *args, **kwargs):
        self._setup_topic()
        return self._conn.subscribe_sqs_queue(self._topic_arn, *args, **kwargs)
