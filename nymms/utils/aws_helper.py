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
    def __init__(self, region, topic_name):
        self.region = region
        self.topic_name = topic_name

        self._conn = None
        self.topic_arn = None

    @property
    def conn(self):
        if not self._conn:
            self._conn = ConnectionManager(self.region).sns
            response = self.conn.create_topic(
                self.topic_name)['CreateTopicResponse']
            self.topic_arn = response['CreateTopicResult']['TopicArn']
        return self._conn

    def publish(self, *args, **kwargs):
        return self.conn.publish(self.topic_arn, *args, **kwargs)

    def subscribe_sqs_queue(self, *args, **kwargs):
        return self.conn.subscribe_sqs_queue(self.topic_arn, *args, **kwargs)
