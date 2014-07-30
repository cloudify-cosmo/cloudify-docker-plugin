#!/usr/bin/env python
# coding: utf-8

import unittest

import test_suite


if __name__ == '__main__':
    testRunner = unittest.TextTestRunner()
    testRunner.run(test_suite.DockerSuite())
