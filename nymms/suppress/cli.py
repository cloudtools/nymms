import time
from nymms.utils.cli import NymmsCommandArgs
import sys
import re
import argparse
from nymms.config import config
import logging

logger = logging.getLogger(__name__)

class SuppressCommandArgs(NymmsCommandArgs):
    def __init__(self, *args, **kwargs):
        super(SuppressCommandArgs, self).__init__(*args, **kwargs)
        self.add_argument('-r', '--region', dest='region',
                help='Override config AWS region to connect to')
        self.add_argument('-d', '--domain', dest='domain',
                help='Override config AWS SDB Domain to use')
        self.region = None
        self.domain = None
        self._now = None
        self.values = None

    def parse_args(self):
        self.values = super(SuppressCommandArgs, self).parse_args()
        return self.values

    def load_config(self):
        # prefer CLI values if we have them
        if self.values.region:
            self.region = self.values.region
        if self.values.domain:
            self.domain = self.values.domain

        # fallback to the config file if we have to
        if not self.domain or not self.region:
            try:
                config.load_config(self.values.config)
            except IOError:
                logger.error("Please specify --region and --domain")
                exit(-1)

            if not self.region:
                self.region = config.settings['region']
            if not self.domain:
                self.domain = config.settings['suppress']['domain']

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
