========
Demo AMI
========

In order to give people something easy to start playing with (and to alleviate
my shame in not having amazing documentation yet) I've gone ahead and started
creating Demo AMIs in Amazon AWS.  These AMIs come up with a complete,
all-in-one (ie: all daemons) instance that has a very basic configuration
that can be used to play with NYMMS and get used to the system.

Currently the AMIs are only being built in **us-west-2 (ie: oregon)** but if
you have interest in running the AMI elsewhere contact me and I'll see about
spinning one up for you.

You can find the AMIs by searching in the EC2 console in **us-west-2** for
**nymms**.  The AMIs are named with a timestamp like so:

*nymms-ubuntu-precise-20131014-215959*

Once you launch the AMI (I suggest using an m1.medium, though it MAY be
possible to use an m1.small) you'll need to provide it with the correct access
to the various AWS services (SQS, SNS, SES, SDB) that NYMMS makes use of.

This can be done one of two ways:

- You can create an instance role with the appropriate permissions (given
  below) and assign the instance to it.
- You can create an IAM user and assign the appropriate permissions then take
  their API credentials and put them in **/etc/default/nymms-common**


The first way is the more secure, but the second is the easiest.  Here's an
example permission policy that should work::

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

Once you've done all that you need to restart each of the three nymms daemons
via upstart so that they can read their new credentials::

    # restart nymms-reactor
    # restart nymms-probe
    # restart nymms-scheduler

If all went well (you can tell by checking out the individual daemon logs in
**/var/log/upstart/**) you should start to see the results of the very basic
monitors in **/var/log/nymms/reactor.log**.

You can find all of the configuration in **/etc/nymms**.

Let me know if you have any questions or run into any issues bringing up the
AMI/services.
