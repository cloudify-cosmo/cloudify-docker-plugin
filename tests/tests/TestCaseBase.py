# coding=utf-8
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import unittest
import logging

import docker

from cloudify.workflows import local
from cloudify import exceptions

from docker_plugin import tasks


_CMD = ('sh -c \'i=0; while [ 1 ]; do i=`expr $i + 1`;'
        '/bin/echo Hello world $i; sleep 1; done\'')
_TEST_PATH = 'tests'


class TestCaseBase(unittest.TestCase):

    def _assert_container_running(self, assert_fun):
        assert_fun(
            self.client.inspect_container(
                self.ctx.runtime_properties['container']
            )['State']['Running']
        )

    def _execute(self):
        inputs = {}
        blueprint_path = os.

    def setUp(self):
        self.client = docker.Client()
