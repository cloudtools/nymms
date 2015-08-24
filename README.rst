===========================================
NYMMS (Not Your Mother's Monitoring System)
===========================================

You can find the latest docs (there aren't enough!) at ReadTheDocs_.

NYMMS is a monitoring framework that takes inspiration from a lot of different
places.

It's goals are:

- Independently scalable components
- Fault tolerant
- Easily useable in a cloud environment
- Easy to add new monitors

There are many other goals, but that's a good start.

Here's a somewhat hard to understand diagram (at least without some
explanation):

.. image:: https://raw.github.com/cloudtools/nymms/master/docs/_static/images/nymms_arch.png

Requirements
============

Currently the main requirements are:

- Python (2.7 - may work on older versions, haven't tested)
- boto
- PyYAML (used in a few backends, will eventually not be a requirement unless
  you need to use those backends)
- Jinja2 (needed for templating)
- Validictory (0.9.1 https://pypi.python.org/pypi/validictory/0.9.1)

Optionally:

- pagerduty (0.2.1 https://pypi.python.org/pypi/pagerduty/0.2.1) if you use the
  pagerduty reactor handler

Docker
======

A docker image is provided that can be used to run any of the daemons used in
NYMMS. It can be pulled from `phobologic/nymms`. To run the daemons, you can
launch them with the following command:

  docker run -e "AWS_ACCESS_KEY_ID=<AWS_ACCESS_KEY_ID>" -e "AWS_SECRET_ACCESS_KEY=<AWS_SECRET_ACCESS_KEY>" --rm -it phobologic/nymms:latest /[scheduler|probe|reactor] <OPTIONAL_ARGS>

For example, to run the scheduler (with verbose logging, the -v) you can run:

  docker run --rm -it phobologic/nymms:latest /scheduler -v

You can also set the `AWS_ACCESS_KEY_ID` & `AWS_SECRET_ACCESS_KEY` in a file,
and then use `--env-file` rather than specifying the variables on the command
line. Optionally, if you are running on a host in EC2 that has an IAM profile
with all the necessary permissions, you do not need to specify the keys at all.

.. _`boto pull request`: https://github.com/boto/boto/pull/1414
.. _`ReadTheDocs`: http://nymms.readthedocs.org/en/latest/
