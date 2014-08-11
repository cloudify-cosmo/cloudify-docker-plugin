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
import time

from docker_plugin import tasks
from tests.TestCaseBase import TestCaseBase

from cloudify import exceptions
from cloudify import mocks


_PORT = 1000
_CMD_CONTAINER_LISTENER = 'nc -nvl {}'.format(_PORT)
_CMD_CONTAINER_BROADCASTER = 'nc -nvz 127.0.0.1 {}'.format(_PORT)


# TODO(Zosia) Rare problem with connection between containers
class TestNetwork(TestCaseBase):
    def _start_container_with_network(self, command, net_mode):
        ctx = mocks.MockCloudifyContext(
            properties=copy.deepcopy(self.ctx.properties)
        )
        ctx.properties['container_create'].update(
            {'command': command}
        )
        self._try_calling(tasks.create, [ctx])
        self._try_calling(tasks.configure, [self.ctx])
        ctx.properties['container_start'].update({'network_mode': net_mode})
        self._try_calling(tasks.run, [ctx])
        return ctx

    def todo_network(self):
        self.listener = self._start_container_with_network(
            _CMD_CONTAINER_LISTENER,
            'bridge'
        )
        time.sleep(1)
        self.broadcaster = self._start_container_with_network(
            _CMD_CONTAINER_BROADCASTER,
            'container:{}'.format(
                self.listener.runtime_properties['container']
            )
        )
        time.sleep(1)
        try:
            self._try_calling(tasks.stop, [self.broadcaster])
        except exceptions.NonRecoverableError:
            pass
        self.assertEqual(
            self.client.inspect_container(
                self.broadcaster.runtime_properties['container']
            )['State']['ExitCode'],
            0
        )

    def tearDown(self):
        def _delete(ctx):
            try:
                self._try_calling(tasks.delete, [ctx])
            except exceptions.NonRecoverableError:
                pass

        _delete(self.listener)
        _delete(self.broadcaster)
