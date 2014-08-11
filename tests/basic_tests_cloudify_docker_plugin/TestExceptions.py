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
from tests.TestCaseBase import TestCaseBase


_WRONG_PATH = 'wrong path'
_WRONG_CMD = 'wrong command'
_DIR = 'wrong_directory'
_MNT_DIR = 'wrong_mnt'
_IMG_SRC = 'image_source'


class TestExceptions(TestCaseBase):
    def test_wrong_path_to_image(self):
        self.ctx.properties['image_build'].update({'path': _WRONG_PATH})
        with self.assertRaises(exceptions.NonRecoverableError):
            self._try_calling(tasks.create, [self.ctx])
        with self.assertRaises(exceptions.NonRecoverableError):
            self._try_calling(tasks.run, [self.ctx])

    def test_wrong_command(self):
        self.ctx.properties['container_create'].update({'command': _WRONG_CMD})
        self._try_calling(tasks.create, [self.ctx])
        with self.assertRaises(exceptions.NonRecoverableError):
            self._try_calling(tasks.run, [self.ctx])

    def test_wrong_volumes(self):
        self._try_calling(tasks.create, [self.ctx])
        self.ctx.properties['container_start'].update(
            {'binds': {_DIR: {'bind': _MNT_DIR}}}
        )
        with self.assertRaises(exceptions.NonRecoverableError):
            self._try_calling(tasks.run, [self.ctx])

    def test_no_image_path(self):
        self.ctx.properties.pop('image_build')
        self.ctx.properties.pop('image_import')
        with self.assertRaises(exceptions.NonRecoverableError):
            self._try_calling(tasks.create, [self.ctx])

    def test_two_image_sources(self):
        self.ctx.properties['image_import'].update({'src': _IMG_SRC})
        with self.assertRaises(exceptions.NonRecoverableError):
            self._try_calling(tasks.create, [self.ctx])
