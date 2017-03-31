
Plugin Requirements
===================

* Python versions:
  * 2.7.x

.. note::

    + The Docker plugin will not install Docker on your host. You need to either use a host with Docker already installed, or you need to install Docker on it.
    + As part of the Docker installation, you should make sure that the user agent, such as ubuntu, is added to the docker group.

    See :ref:`os_example` for an example node type which will set up a suitable host on OpenStack.

Compatibility
=============

The Docker plugin uses Docker-Py version 1.2.3.

