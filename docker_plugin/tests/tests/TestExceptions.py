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

from docker_plugin import tasks
from tests.tests.TestCaseBase import TestCaseBase


_WRONG_PATH = 'wrong path'
_WRONG_CMD = 'wrong command'
_DIR = 'wrong_directory'
_MNT_DIR = 'wrong_mnt'
_IMG_SRC = 'image_source'


class TestExceptions(TestCaseBase):
    def test_wrong_path_to_image(self):
        def assertion(op, message):
            try:
                self._execute([op], image_build={'path': _WRONG_PATH})
                self.fail()
            except exceptions.NonRecoverableError as e:
                self.assertIn(message, e.message)
        assertion('create', 'No such file')
        assertion('configure', 'No image specified')
        assertion('run', 'No container specified')

    def test_wrong_command(self):
        try:
            self._execute(['create', 'configure', 'run'],
                          container_config={'command': _WRONG_CMD})
            self.fail()
        except exceptions.NonRecoverableError as e:
            self.assertIn('"wrong": executable file not found', e.message)

    def test_wrong_volumes(self):
        try:
            self._execute(['create', 'configure', 'run'],
                          container_start={'binds': {_DIR: {'bind': _MNT_DIR}}})
            self.fail()
        except exceptions.NonRecoverableError as e:
            self.assertIn('cannot bind mount volume', e.message)

    def test_no_image_path(self):
        try:
            self._execute(['create'],
                          image_build={'stub': 'prop'})
            self.fail()
        except exceptions.NonRecoverableError as e:
            self.assertIn('Either path or url', e.message)

    def test_two_image_sources(self):
        try:
            self._execute(['create'],
                          image_import={'src': _IMG_SRC})
            self.fail()
        except exceptions.NonRecoverableError as e:
            self.assertIn('There can only be one image source', e.message)
