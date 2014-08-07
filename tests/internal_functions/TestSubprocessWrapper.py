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


from cloudify import exceptions

from docker_plugin import docker_wrapper

from tests.TestWithMockupCtx import TestWithMockupCtx
from docker_plugin import subprocess_wrapper


_VALID_PROCESS = 'tests/internal_functions/basic_script.sh'
_SUCCESS_EXIT_CODE = 0

_HUNG_UP_SLEEP_TIME = 100
_HUNG_UP_PROCESS = '{} {}'.format(_VALID_PROCESS, _HUNG_UP_SLEEP_TIME)
_HUNG_UP_EXIT_CODE = 10

_HUNG_UP_ON_TERMINATE = 100
_HUNG_UP_ON_TERMINATE_PROCESS = '{} {} {}'.format(
    _VALID_PROCESS,
    _HUNG_UP_SLEEP_TIME,
    _HUNG_UP_ON_TERMINATE
)
_HUN_UP_ON_TERMINATE_EXIT_CODE = -9

_MAX_WAITING_TIME = 10
_TIMEOUT_TERMINATE = 5

_VAL1 = 'stdout 1'
_VAL2 = 'stdout 2'
_VALE1 = 'stderr 1'
_VALE2 = 'stderr 2'
_VAL3 = 'terminate'
_VALID_VALUES = [
    (_VAL1, True),
    (_VAL2, True),
    (_VALE1, True),
    (_VALE2, True),
    (_VAL3, False)
]
_INVALID_VALUES = [
    (_VAL1, True),
    (_VAL2, False),
    (_VALE1, True),
    (_VALE2, False),
    (_VAL3, True)
]


class TestSubprocessWrapper(TestWithMockupCtx):
    def _assert_process_values(self, process, expected_exit_code, values):
        return_code, stdout, stderr = subprocess_wrapper.run_process(
            self.ctx,
            process,
            _MAX_WAITING_TIME,
            _TIMEOUT_TERMINATE
        )
        self.assertEqual(return_code, expected_exit_code)
        for v in values:
            if (v[1]):
                self.assertTrue(v[0] in stdout or v[0] in stderr)
            else:
                self.assertFalse(v[0] in stdout or v[0] in stderr)

    def test_run_valid_process(self):
        self._assert_process_values(
            _VALID_PROCESS,
            _SUCCESS_EXIT_CODE,
            _VALID_VALUES
        )

    def test_run_hung_up_process(self):
        self._assert_process_values(
            _HUNG_UP_PROCESS,
            _HUNG_UP_EXIT_CODE,
            _INVALID_VALUES
        )

    def test_run_hung_up_on_terminate(self):
        self._assert_process_values(
            _HUNG_UP_ON_TERMINATE_PROCESS,
            _HUN_UP_ON_TERMINATE_EXIT_CODE,
            _INVALID_VALUES
        )
