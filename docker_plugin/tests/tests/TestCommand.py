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


from docker_plugin.tests.tests import TestCaseBase


_CMD_SUCC = '/bin/true'
_CMD_FAIL = '/bin/false'


class TestCommand(TestCaseBase.TestCaseBase):
    def _check_command(self, command, assert_fun):
        container_config = {'command': command}
        self._execute(['create', 'configure', 'run', 'stop'],
                      container_config=container_config)
        assert_fun(
            self.client.inspect_container(
                self.runtime_properties['container']
            )['State']['ExitCode']
        )

    def test_command_success(self):
        self._check_command(
            _CMD_SUCC,
            lambda exit_code: self.assertEqual(exit_code, 0)
        )

    def test_command_failure(self):
        self._check_command(
            _CMD_FAIL,
            lambda exit_code: self.assertNotEqual(exit_code, 0)
        )
