import copy

from docker_plugin import tasks
from TestCaseBase import TestCaseBase

from cloudify import mocks


_PORT = 1000
_MSG = 'Hello'
_CMD_CONTAINER_BROADCASTER = 'nc -l {}'.format(_PORT)
_CMD_CONTAINER_LISTENER = 'nc -z 127.0.0.1 1000'
_BROADCASTER_NAME = 'broadcaster'


class TestNetwork(TestCaseBase):
    def _start_container_with_network(self, command, net_mode, name):
        ctx = mocks.MockCloudifyContext(
            properties=copy.deepcopy(self.ctx.properties)
        )
        ctx.properties['container_create'].update(
            {'command': command, 'name': name}
        )
        tasks.create(ctx)
        ctx.properties['container_start'].update({'network_mode': net_mode})
        tasks.run(ctx)
        return ctx

    def runTest(self):
        self.broadcaster = self._start_container_with_network(
            _CMD_CONTAINER_BROADCASTER,
            'bridge',
            _BROADCASTER_NAME
        )
        self.listener = self._start_container_with_network(
            _CMD_CONTAINER_LISTENER,
            'container:{}'.format(_BROADCASTER_NAME),
            'listener'
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
