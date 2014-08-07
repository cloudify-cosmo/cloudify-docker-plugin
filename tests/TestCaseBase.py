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

from TestWithMockupCtx import TestWithMockupCtx


_CMD = ('sh -c \'i=0; while [ 1 ]; do i=`expr $i + 1`;'
        '/bin/echo Hello world $i; sleep 1; done\'')
_TEST_PATH = 'tests'


class TestCaseBase(TestWithMockupCtx):
    def _assert_container_running(self, assert_fun):
        assert_fun(
            self.client.inspect_container(
                self.ctx.runtime_properties['container']
            )['State']['Running']
        )

    def setUp(self):
        super(TestCaseBase, self).setUp()
        example_properties = {
            'daemon_client': {},
            'image_build': {
                'path': _TEST_PATH,
                'rm': True
            },
            'container_create': {
                'command': _CMD
            },
            'container_start': {},
            'container_stop': {},
            'container_remove': {},
            'image_import': {}
        }
        self.ctx.properties.update(example_properties)

    def tearDown(self):
        # Try to delete container,
        # if it fails, because it doesnt exist, do nothing
        try:
            tasks.delete(self.ctx)
        except exceptions.NonRecoverableError:
            pass
