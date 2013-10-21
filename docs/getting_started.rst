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

I maintain a set of packages for installing NYMMS on your Ubuntu Precise
system.  In order to install these you first need to add my PPA & key to your
sources.  You can find the directions to do so
`here <https://launchpad.net/~loki77/+archive/nymms>`_.

Once you've done that, you can use apt to download the packages::

    apt-get install python-nymms
    apt-get install nymms-common
    apt-get install nymms-reactor nymms-probe nymms-scheduler

The first package is the python code that makes up NYMMS.  The second package
is some common configuration used by Ubuntu for running the NYMMS daemons.  The
last three packages are mainly startup scripts for starting NYMMS via Ubuntu's
`Upstart`_ system.

Once those packages are installed you only need to provide NYMMS with the
correct AWS permissions in order to access the various services it makes use
of.  See `Permissions`_ below.

.. note::

    If you decide to provide the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
    environment variables for a user, you can store them in
    /etc/default/nymms-common.  Be sure to restart each of the daemons after
    doing so.

These packages will include a basic config as well as a few example nodes,
monitors and handlers to give an example of how the system runs.  You can
control the stopping/starting of all the daemons with various upstart
commands - there is one upstart script per daemon.  For example to restart all
three daemons you would call::

    restart nymms-reactor
    restart nymms-probe
    restart nymms-scheduler

.. _`Upstart`: http://upstart.ubuntu.com/cookbook/


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
