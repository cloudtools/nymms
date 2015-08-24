==========================
Getting Started with NYMMS
==========================

This tutorial will walk you through installing and configuring NYMMS.  If you'd
quickly like to start a NYMMS system to play with yourself, please see
the :doc:`Demo AMI <demo>` documentation.

This tutorial assumes basic understanding of `Amazon Web Services`_.  You will
either need to understand how to launch an instance with an `instance profile`_
with the appropriate permissions (see below) or you will need the
``Access Key ID`` and ``Secret Access Key`` for a user with the appropriate
permissions.


----------------
Installing NYMMS
----------------

On Ubuntu
=========

Maintaining the Ubuntu packages proved to be difficult after NYMMS started
using multiple third party python packages. Because of that, we no longer
maintain the Ubuntu packages. Instead you should use the docker images (see
below)

Using Docker
============

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

The docker container has the example config, which just checks that
`www.google.com` is alive. It only has a single reactor handler enabled, the
log handler, which logs to `/var/log/nymms/reactor.log`.

To use the docker container with your own configs, you should put them in a
directory, then mount it as a volume when you run the containers. If you put
the configs in the directory `/etc/nymms` on the host, you should run the
container like this:

  docker run -v /etc/nymms:/etc/nymms:ro --rm -it phobologic/nymms:latest /scheduler -v

Using PIP
=========

Since NYMMS is written in python I've also published it to `PyPI`_.  You can
install it with pip by running::

    pip install nymms

.. warning::

    The python library does not come with startup scripts, though it does
    install the three daemon scripts in system directories.  You should work on
    your own startup scripts for the OS you are using.

.. _`PyPI`: https://pypi.python.org/pypi

Installing From Source
======================

You can also install from the latest source repo::

    git clone https://github.com/cloudtools/nymms.git
    cd nymms
    python setup.py install

.. warning::

    The python library does not come with startup scripts, though it does
    install the three daemon scripts in system directories.  You should work on
    your own startup scripts for the OS you are using.

Using Virtual Environments
===========================

Another common way to install ``NYMMS`` is to use a `virtualenv`_ which
provides isolated environments.  This is also useful if you want to play with
``NYMMS`` but do not want to (or do not have the permissions to) install it as
root.  First install the ``virtualenv`` Python package::

    pip install virtualenv

Next you'll need to create a virtual environment to work in with the newly
installed ``virtualenv`` command and specifying a directory where you want
the virtualenv to be created::

    mkdir ~/.virtualenvs
    virtualenv ~/.virtualenvs/nymms

Now you need to activate the virtual environment::

    source ~/.virtualenvs/nymms/bin/activate

Now you can use either the instructions in `Using PIP`_ or 
`Installing From Source`_ above.

When you are finished using ``NYMMS`` you can deactivate your virtual
environment with::

    deactivate

.. note::

    The deactivate command just unloads the virtualenv from that session.
    The virtualenv still exists in the location you created it and can be
    re-activated by running the activate command once more.

.. _`virtualenv`: http://www.virtualenv.org/en/latest/


-----------
Permissions
-----------

NYMMS makes use of many of the `Amazon Web Services`_.  In order for the
daemons to use these services they have to be given access to them.  Since
NYMMS is written in python, we make heavy use of the `boto`_ library.
Because of that we fall back on boto's way of dealing with credentials.

If you are running NYMMS on an EC2 instance the preferred way to provide
access is to use an `instance profile`_.  If that is not possible (you do not
run on EC2, or you don't understand how to setup the instance profile, etc)
then the next best way of providing the credentials is by createing an `IAM`_
user with only the permissions necessary to run NYMMS.  You would then need
to get that user's Access Key ID & Secret Key and provide them as the
environment variables ``AWS_ACCESS_KEY_ID`` and ``AWS_SECRET_ACCESS_KEY``.

Whichever method you choose, you'll need to provide the following permission
document (for either the user, or the role)::

    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Action": [
            "ses:GetSendQuota",
            "ses:SendEmail"
          ],
          "Sid": "NymmsSESAccess",
          "Resource": [
            "*"
          ],
          "Effect": "Allow"
        },
        {
          "Action": [
            "sns:ConfirmSubscription",
            "sns:CreateTopic",
            "sns:DeleteTopic",
            "sns:GetTopicAttributes",
            "sns:ListSubscriptions",
            "sns:ListSubscriptionsByTopic",
            "sns:ListTopics",
            "sns:Publish",
            "sns:SetTopicAttributes",
            "sns:Subscribe",
            "sns:Unsubscribe"
          ],
          "Sid": "NymmsSNSAccess",
          "Resource": [
            "*"
          ],
          "Effect": "Allow"
        },
        {
          "Action": [
            "sqs:ChangeMessageVisibility",
            "sqs:CreateQueue",
            "sqs:DeleteMessage",
            "sqs:DeleteQueue",
            "sqs:GetQueueAttributes",
            "sqs:GetQueueUrl",
            "sqs:ListQueues",
            "sqs:ReceiveMessage",
            "sqs:SendMessage",
            "sqs:SetQueueAttributes"
          ],
          "Sid": "NymmsSQSAccess",
          "Resource": [
            "*",
          ],
          "Effect": "Allow"
        },
        {
          "Action": [
            "sdb:*"
          ],
          "Sid": "NymmsSDBAccess",
          "Resource": [
            "*"
          ],
          "Effect": "Allow"
        }
      ]
    }

.. note::

    If you want to provide even tighter permissions, you can limit the SNS, SDB
    and SQS stanzas to specific resources.  You should provide the ARNs for
    each of the resources necessary.


-------------
Configuration
-------------

Please see the :doc:`configuration <config>` page for information on how to
configure ``NYMMS``.  Usually the configuration files are located in
``/etc/nymms/config`` but that is not a requirement and all of the daemons
accept the ``--config`` argument to point them at a new config file.


.. _`Amazon Web Services`: https://aws.amazon.com/
.. _`AWS`: https://aws.amazon.com/
.. _`boto`: https://github.com/boto/boto
.. _`instance profile`: http://docs.aws.amazon.com/IAM/latest/UserGuide/instance-profiles.html
.. _`IAM`: http://aws.amazon.com/iam/
