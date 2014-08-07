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


import socket

from docker_plugin import tasks
from tests.TestCaseBase import TestCaseBase


_INTERFACE = '127.0.0.1'
_HOST = _INTERFACE
_PORT1 = 1234
_PORT2 = 1235
_CMD = '/bin/nc -nvl {}'.format(str(_PORT1))


class TestPortsConfig(TestCaseBase):

    def test_ports_config(self):
        tasks.create(self.ctx)
        tasks.run(self.ctx)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((_HOST, _PORT2))
            s.close()
        except socket.error as e:
            raise AssertionError(e)

    def setUp(self):
        super(TestPortsConfig, self).setUp()
        self.ctx.properties['container_create'].update({'command': _CMD})
        self.ctx.properties['container_create'].update({'ports': [_PORT1]})
        self.ctx.properties['container_start'].update(
            {'port_bindings': {_PORT1: (_INTERFACE, _PORT2)}}
        )
