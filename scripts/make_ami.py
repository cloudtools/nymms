#!/usr/bin/env python

import time
import urllib2
import argparse

import yaml
from boto.exception import EC2ResponseError
from boto.ec2 import connect_to_region, RegionData

from nymms.utils.commands import execute, CommandFailure, CommandTimeout
from nymms.utils import logutil

regions = RegionData.keys()


def get_ubuntu_ami(requested_region, release='precise'):
    ubuntu_url = ('http://cloud-images.ubuntu.com/query/%s/server/'
                  'released.current.txt') % (release)
    logger.debug("Getting ami for region %s from %s.", requested_region,
                 ubuntu_url)
    lines = urllib2.urlopen(ubuntu_url).read().split('\n')
    for l in lines:
        # skip blank lines
        if not l:
            continue
        # Split the tab separated list
        entries = l.split('\t')
        (disk, cpu, region, ami) = entries[4:8]
        virtual = entries[10]
        if disk == 'ebs' and cpu == 'amd64' and virtual == 'paravirtual':
            if region == requested_region:
                logger.debug("Found ami %s.", ami)
                return ami
    raise ValueError("AMI for region '%s' not found" % requested_region)


def wait_for_instance_state(instance, state, timeout=None):
    logger.debug("Waiting for instance %s to enter %s state...", instance.id,
                 state)
    waited = 1
    while instance.update() != state:
        if timeout and waited > timeout:
            return None
        if waited % 5 == 0:
            logger.debug("Instance has taken %d seconds...", waited)
        waited += 1
        time.sleep(1)
    logger.debug("Instance in %s state.", state)
    return True


def generate_cloud_config():
    sources = [
        {
            'source': 'deb http://ppa.launchpad.net/chris-lea/python-boto/'
                      'ubuntu precise main',
            'keyid': 'C7917B12',
            'filename': 'boto.list'
        },
        {
            'source': 'deb http://ppa.launchpad.net/loki77/nymms/ubuntu '
                      'precise main',
            'keyid': 'A835227D',
            'filename': 'nymms.list'
        },
    ]

    packages = ['python-yaml', 'python-jinja2', 'python-boto', 'python-nymms',
                'nymms-common', 'nymms-scheduler', 'nymms-probe',
                'nymms-reactor', 'nagios-plugins', 'python-pip']

    commands = ['pip install validictory']

    cloud_config = {'apt_sources': sources,
                    'packages': packages,
                    'runcmd': commands}
    return "#cloud-config\n" + yaml.dump(cloud_config)


def check_finish_install(address):
    attempt = 0
    while True:
        attempt += 1
        try:
            out = execute("ssh ubuntu@%s status cloud-config" % (address),
                          timeout=30).strip()
            if out == 'cloud-config stop/waiting':
                logger.debug('cloud-config finished')
                break
            else:
                logger.debug(out.strip())
        except CommandTimeout:
            logger.debug("ssh to %s timed out.", address)
        except CommandFailure, e:
            logger.debug("Command failed with exit code %d.", e.return_code)
            for i in e.output.split('\n'):
                logger.debug("    stdout: %s", i)
        time.sleep(5)


def publish_ami(image_id):
    logger.debug("Publishing AMI %s to the world.", image_id)
    while True:
        try:
            ami = conn.get_image(image_id)
            break
        except EC2ResponseError:
            logger.debug("AMI does not exist yet.")
            time.sleep(2)

    while True:
        try:
            ami.set_launch_permissions(group_names=['all'])
            logger.info("AMI %s published.", image_id)
            break
        except EC2ResponseError:
            sleep_time = 30
            logger.debug("AMI not ready. Sleeping %d seconds.", sleep_time)
            time.sleep(sleep_time)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Used to create a new NYMMS example AMI.')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='Verbose output.  Can be specified up to two '
                             'times.')
    parser.add_argument('-k', '--ssh-key', default='default',
                        help="SSH Keypair to use. Default: %(default)s")
    parser.add_argument('-t', '--instance-type', default='m3.medium',
                        help="Instance type to use to build AMI. "
                             "Default: %(default)s")
    parser.add_argument('-g', '--security-group', default='default',
                        help="Security group of instance used to build the "
                             "AMI.  Must allow SSH (tcp port 22). "
                             "Default: %(default)s")
    parser.add_argument('region', choices=regions,
                        help='The region to build the ami in.')

    args = parser.parse_args()

    log_level = logutil.INFO
    if args.verbose:
        log_level = logutil.DEBUG
    logger = logutil.setup_root_logger(stdout=log_level)
    if not args.verbose > 2:
        logutil.quiet_boto_logging()

    base_image_id = get_ubuntu_ami(args.region)
    logger.info("Building from base ubuntu AMI %s.", base_image_id)
    logger.debug("Connecting to EC2 API in region %s.", args.region)
    conn = connect_to_region(args.region)
    base_ami = conn.get_image(base_image_id)
    logger.debug("Launching instance with AMI %s.", base_image_id)
    reservation = base_ami.run(key_name=args.ssh_key,
                               security_groups=[args.security_group, ],
                               user_data=generate_cloud_config(),
                               instance_type=args.instance_type)
    instance = reservation.instances[0]
    wait_for_instance_state(instance, 'running')
    logger.debug('Instance up, public IP: %s', instance.ip_address)
    logger.debug('Sleeping for 30 seconds for instance to finish booting.')
    time.sleep(30)
    check_finish_install(instance.ip_address)
    logger.debug('Shutting down instance.')
    instance.stop()
    wait_for_instance_state(instance, 'stopped')
    ami_name = time.strftime("nymms-ubuntu-precise-%Y%m%d-%H%M%S")
    logger.debug("Creating image %s.", ami_name)
    image_id = conn.create_image(instance.id, ami_name)
    publish_ami(image_id)
    logger.debug("Terminating instance %s.", instance.id)
    instance.terminate()
