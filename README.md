Cloudify Docker plugin
======================

A Cloudify plugin enabling it to create and manipulate Docker containers.


Installation and upgrading
--------------------------

To install run: `python setup.py install`.

To upgrade only this package run: `pip install --no-deps --upgrade .`.


Running tests
-------------

Test requirements have been emplaced in `dev_*.txt` files, as `setuptools`
do not install requirements listed in `test_requires`. You may use those files
to force setuptools to automatically install needed packages.

Currently, the `cloudify-system-tests` package does not contain anything but
the `__init__.py` file. This issue can be easily worked around by installing
all the requirements and copying the entire `cosmo_tester` directory into
the plugin's root.


Tips
----

Installing *python-apt* with *pip* on *Ubuntu 14.04* `*trusty*':

    sudo apt-get purge python-apt
    sudo apt-get install g++ python-dev ibapt-pkg-dev
    sudo pip install python-apt
