===========================================
NYMMS (Not Your Mother's Monitoring System)
===========================================

NYMMS is a monitoring framework that takes inspiration from a lot of different
places.

It's goals are:

- Independently scalable components
- Fault tolerant
- Easily useable in a cloud environment
- Easy to add new monitors

There are many other goals, but that's a good start.

Requirements
============

Currently the main requirements are:

- Python (2.7 - may work on older versions, haven't tested)
- boto (It currently requires this `boto pull request`_, which is very close to
  being accepted)
- PyYAML (used in a few backends, will eventually not be a requirement unless
  you need to use those backends)
- Jinja2 (needed for templating)

.. _`boto pull request`: https://github.com/boto/boto/pull/1414
