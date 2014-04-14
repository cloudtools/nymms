import time
import sys
import re
import argparse
from nymms.utils.cli import NymmsCommandArgs
import logger



class SuppressCommandArgs(NymmsCommandArgs):
    def __init__(self, *args, **kwargs):
        super(SuppressCommandArgs, self).__init__(*args, **kwargs)
        self.add_argument('-r', '--region', dest='region',
                help='Override config AWS region to connect to')
        self.add_argument('-d', '--domain', dest='domain',
                help='Override config AWS SDB Domain to use')
        self.region = None
        self.domain = None
        self.reference_time = int(time.time())
        self.values = None

    def parse_args(self):
        self.values = super(SuppressCommandArgs, self).parse_args()
        return self.values

    def load_config(self):
        # load nymms.config here to avoid the error: 
        # No handlers could be found for logger "nymms.config.config"
        from nymms.config import config

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

    def parse_time(self, expires):
        """Parses a time in YYYYMMDDHHMMSS or +XXXX[smhd] and returns
        epoch time

        if expires == 0, returns None"""
        if expires == '0':
            return None

        if expires[0] == '+' or expires[0] == '-':
            last_char = expires[len(expires) - 1]
            user_value = expires[0:(len(expires) - 1)]
            if last_char == 's':
                epoch = self.reference_time + int(user_value)
            elif last_char == 'm':
                epoch = self.reference_time + (int(user_value) * 60)
            elif last_char == 'h':
                epoch = self.reference_time + (int(user_value) * 60 * 60)
            elif last_char == 'd':
                epoch = self.reference_time + (int(user_value) * 60 * 60 * 24)
            else:
                sys.stderr.write("Invalid time format: %s.  " +
                        "Missing s/m/h/d qualifier\n", expires)
                exit(-1)
        else:
            epoch = int(time.strftime("%s",
                time.strptime(expires, "%Y%m%d%H%M%S")))

        return epoch
