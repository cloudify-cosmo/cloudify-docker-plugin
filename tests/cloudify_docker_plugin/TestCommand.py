import time

from docker_plugin import tasks
from TestCaseBase import TestCaseBase


_CMD_SUCC = '/bin/true'
_CMD_FAIL = '/bin/false'


class TestCommand(TestCaseBase):
    def _check_command(self, command, assert_fun):
        self.ctx.properties['container_create'].update({'command': command})
        tasks.create(self.ctx)
        tasks.run(self.ctx)
        tasks.stop(self.ctx)
        assert_fun(
            self.client.inspect_container(
                self.ctx.runtime_properties['container']
            )['State']['ExitCode']
        )

    def command_success(self):
        self._check_command(
            _CMD_SUCC,
            lambda exit_code: self.assertEqual(exit_code, 0)
        )

    def command_failure(self):
        self._check_command(
            _CMD_FAIL,
            lambda exit_code: self.assertNotEqual(exit_code, 0)
        )
