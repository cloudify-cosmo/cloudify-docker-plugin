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


import copy

from docker_plugin import tasks
from tests.TestCaseBase import TestCaseBase

from cloudify import exceptions
from cloudify import mocks


_PORT = 1000
_MSG = 'Hello'
_CMD_CONTAINER_BROADCASTER = 'nc -l {}'.format(_PORT)
_CMD_CONTAINER_LISTENER = 'nc -z 127.0.0.1 1000'


class TestNetwork(TestCaseBase):
    def _start_container_with_network(self, command, net_mode):
        ctx = mocks.MockCloudifyContext(
            properties=copy.deepcopy(self.ctx.properties)
        )
        ctx.properties['container_create'].update(
            {'command': command}
        )
        tasks.create(ctx)
        ctx.properties['container_start'].update({'network_mode': net_mode})
        tasks.run(ctx)
        return ctx

    def test_network(self):
        self.broadcaster = self._start_container_with_network(
            _CMD_CONTAINER_BROADCASTER,
            'bridge'
        )
        self.listener = self._start_container_with_network(
            _CMD_CONTAINER_LISTENER,
            'container:{}'.format(self.broadcaster.runtime_properties['container'])
        )
        try:
            tasks.stop(self.listener)
        except exceptions.NonRecoverableError:
            pass
        self.assertEqual(
            self.client.inspect_container(
                self.listener.runtime_properties['container']
            )['State']['ExitCode'],
            0
        )

    def tearDown(self):
        def _delete(ctx):
            try:
                tasks.delete(ctx)
            except exceptions.NonRecoverableError:
                pass

        _delete(self.broadcaster)
        _delete(self.listener)
