Cloudify Docker plugin
======================

A Cloudify plugin enabling it to create and manipulate Docker containers.


Installation and upgrading
--------------------------

To install run: `python setup.py install`.

To upgrade only this package run: `pip install --no-deps --upgrade .`.


Tips
----

Installing *python-apt* with *pip* on *Ubuntu 14.04* `*trusty*':

    sudo apt-get purge python-apt
    sudo apt-get install g++ python-dev ibapt-pkg-dev
    sudo pip install python-apt
