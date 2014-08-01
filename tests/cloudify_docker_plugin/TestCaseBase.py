import unittest

import docker

from cloudify import exceptions
from cloudify import mocks

from docker_plugin import tasks


_CMD = ('sh -c \'i=0; while [ 1 ]; do i=`expr $i + 1`;'
        '/bin/echo Hello world $i; sleep 1; done\'')
_TEST_PATH = 'tests'


class TestCaseBase(unittest.TestCase):

    ctx = None
    client = None

    def _assert_container_running(self, assert_fun):
        assert_fun(
            self.client.inspect_container(
                self.ctx.runtime_properties['container']
            )['State']['Running']
        )

    def setUp(self):
        self.client = docker.Client()
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
        self.ctx = mocks.MockCloudifyContext(properties=example_properties)
        # TODO(Zosia) temporary debug help
        self.ctx.logger.info('\n'+str(self.id)+'\n')

    def tearDown(self):
        # Try to delete container,
        # if it fails, because it doesnt exist, do nothing
        try:
            tasks.delete(self.ctx)
        except (docker.errors.APIError, KeyError):
            pass
