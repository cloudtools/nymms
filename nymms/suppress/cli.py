import time
from nymms.config import config
import sys
import re

DEFAULT_REGION = 'us-east-1'
DEFAULT_DOMAIN = 'reactor_suppress'


class SuppressCLI(object):
    def __init__(self, parser):
        self.parser = parser
        self.parser.add_argument('-C', '--config', dest='config',
                default='/etc/nymms/config.yaml',
                help='NYMMS config file')
        self.parser.add_argument('-r', '--region', dest='region',
                help='Override config AWS region to connect to')
        self.parser.add_argument('-d', '--domain', dest='domain',
                help='Override config AWS SDB Domain to use')
        self.region = None
        self.domain = None
        self._now = None

    def add_argument(self, *args, **kwargs):
        self.parser.add_argument(*args, **kwargs)

    def values(self):
        self.values = self.parser.parse_args()

        # default is config file
        try:
            config.load_config(self.values.config)
            self.region = config.settings['region']
            self.domain = config.settings['suppress']['domain']
        except:
            # there may not be a config file or it might be old
            pass
        # override with cli options
        if self.values.region:
            self.region = self.values.region
        if self.values.domain:
            self.domain = self.values.domain
        # if not set via cli or config, use defaults
        if not self.region:
            self.region = DEFAULT_REGION
        if not self.domain:
            self.domain = DEFAULT_DOMAIN
        return self.values

    def now(self, reset=False):
        if self._now and not reset:
            return self._now

        self._now = int(time.time())
        return self._now

    def parse_time(self, expires):
        """Parses a time in YYYYMMDDHHMMSS or +XXXX[smhd] and returns
        epoch time

        if expires == 0, returns None"""
        if expires == '0':
            return None

        now = self.now()
        if expires[0] == '+' or expires[0] == '-':
            last_char = expires[len(expires) - 1]
            user_value = expires[0:(len(expires) - 1)]
            if last_char == 's':
                epoch = now + int(user_value)
            elif last_char == 'm':
                epoch = now + (int(user_value) * 60)
            elif last_char == 'h':
                print "user_value: %s" % (user_value,)
                epoch = now + (int(user_value) * 60 * 60)
            elif last_char == 'd':
                epoch = now + (int(user_value) * 60 * 60 * 24)
            else:
                sys.stderr.write("Invalid time format: %s.  " +
                        "Missing s/m/h/d qualifier\n", expires)
                exit(-1)
        else:
            regex = re.compile('(\d{4})(\d{2}){5}')
            match = regex.match(expires)
            epoch = int(time.strftime("%Y%m%d%H%M%S", (match[0], match[1],
                match[2], match[3], match[4], match[5])))
        return epoch
