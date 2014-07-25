import unittest

import docker

from cloudify import exceptions
from cloudify import mocks

from docker_plugin import tasks


class TestCaseBase(unittest.TestCase):

    ctx = None
    client = None

    def setUp(self):
        # TODO temporary debug help
        print('\n'+str(self.id)+'\n')
        self.client = docker.Client()
        example_properties = {
            'daemon_client': {},
            'image': {
                'path': 'tests',
                'rm': True
            },
            'container_create': {
                'command': ("sh -c 'i=0; while [ 1 ]; do i=`expr $i + 1`;"
                            "/bin/echo Hello world $i; sleep 1; done'")
            },
            'container_start': {},
            'container_stop': {},
            'container_remove': {},
            'image_import': {}
        }
        self.ctx = mocks.MockCloudifyContext(properties=example_properties)

    def tearDown(self):
        try:
            tasks.delete(self.ctx)
        except (docker.errors.APIError, KeyError):
            # Try to delete container,
            # if it fails, because it doesnt exist, do nothing
            pass
