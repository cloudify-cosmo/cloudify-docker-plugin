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

from tests.tests.TestCaseBase import TestCaseBase


_DIR = '/tmp/test_folder.{}'.format(str(os.getpid()))
_FILE = 'test_file'
_FILE_PATH = '{}/{}'.format(_DIR, _FILE)
_MNT_DIR = '/mnt'
_CONT_FILE_PATH = '{}/{}'.format(_MNT_DIR, _FILE)
_TEXT = 'Sample text\n'  # The '\n' is **extremely** important.
_CMD = 'sh -c \'/bin/cat {}; sleep 1\''.format(_CONT_FILE_PATH)


class TestVolumes(TestCaseBase):

    def test_volumes(self):
        self._execute(
            ['create', 'configure', 'run'],
            container_config={
                'volumes': [_MNT_DIR],
                'command': _CMD
            },
            container_start={
                'binds': {_DIR: {'bind': _MNT_DIR}}
            }
        )
        logs = self.client.logs(self.runtime_properties['container'])
        self.assertEqual(logs, _TEXT)

    def setUp(self):
        super(TestVolumes, self).setUp()
        os.mkdir(_DIR, 0755)
        with open(_FILE_PATH, 'w') as f:
            f.write(_TEXT)

    def tearDown(self):
        os.remove(_FILE_PATH)
        os.rmdir(_DIR)
        super(TestVolumes, self).tearDown()
