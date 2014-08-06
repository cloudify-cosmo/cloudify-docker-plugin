#!/bin/sh

export CLOUDIFY_TEST_MANAGEMENT_IP=127.0.0.1

nosetests -sv tests/system_tests/TestPluginNetworking.py

