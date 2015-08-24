FROM phusion/baseimage:0.9.17
MAINTAINER Michael Barrett <loki77@gmail.com>

RUN apt-get update && apt-get -y install nagios-plugins ncurses-dev libreadline-dev python-dev python-setuptools libyaml-dev && easy_install pip && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN adduser --system nymms; mkdir -p /var/log/nymms; chown -R nymms /var/log/nymms

COPY . /src
RUN cd /src; python setup.py install

COPY docker/conf /etc/nymms
COPY docker/scheduler /scheduler
COPY docker/reactor /reactor
COPY docker/probe /probe

CMD ["/sbin/my_init"]
