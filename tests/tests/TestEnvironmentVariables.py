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


from docker_plugin import tasks
from docker_plugin import docker_wrapper
from tests.tests.TestCaseBase import TestCaseBase


_KEY1 = 'a'
_KEY2 = 3
_KEY3 = 'b'
_VAL1 = 10
_VAL2 = {'x': [], 'y': 'value'}
_VAL3 = []
_ADKEY1 = 'c'
_ADKEY2 = _KEY3
_ADVAL1 = '1'
_ADVAL2 = '2'

_ENV_VAR = {
    _KEY1: _VAL1,
    _KEY2: _VAL2,
    _KEY3: _VAL3
}

_ENV_LIST = [
    '{}={}'.format(str(_KEY1), str(_VAL1)),
    '{}={}'.format(str(_KEY2), str(_VAL2)),
    '{}={}'.format(str(_KEY3), str(_VAL3))
]

_ADDITIONAL_ENV = {_ADKEY1: _ADVAL1, _ADKEY2: _ADVAL2}
_ADDITIONAL_ENV_LIST = [
    '{}={}'.format(_ADKEY1, _ADVAL1),
    '{}={}'.format(_ADKEY2, _ADVAL2)
]

class TestEnvironmentVariables(TestCaseBase):
    def _check_env(self, docker_env_var, environment, env_set):
        def assertion(**kwargs):
            inspect_dict = docker_wrapper.inspect_container(self.client)
            self.assertTrue(env_set.issubset(set(inspect_dict['Config']['Env'])))
        self.patch_custom_operation(assertion)
        self._execute(['set_docker_env_var', 'create', 'configure', 'run',
                       'custom_operation'],
                      docker_env_var=docker_env_var,
                      container_config={
                        'environment': environment
                      })

    def test_basic(self):
        self._check_env(_ENV_VAR, {}, set(_ENV_LIST))

    def test_with_additional_env(self):
        self._check_env(_ENV_VAR, _ADDITIONAL_ENV, set(_ADDITIONAL_ENV_LIST))
