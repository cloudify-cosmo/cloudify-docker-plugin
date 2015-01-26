########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

# Built-in Imports
import time
import json

# Third Party Imports
import testtools
from docker import Client
from docker import errors

# Cloudify Imports is imported and used in operations
from docker_plugin import tasks
from cloudify.mocks import MockCloudifyContext
from cloudify.exceptions import NonRecoverableError


class TestStart(testtools.TestCase):

    def get_client(self, daemon_client):
        try:
            return Client(**daemon_client)
        except errors.DockerException as e:
            raise NonRecoverableError('Error while getting client: '
                                      '{0}.'.format(str(e)))

    def mock_ctx(self, test_name):
        """ Creates a mock context for the instance
            tests
        """

        test_node_id = test_name
        test_properties = {
            '': 'cloudify-test-container',
            'use_external_resource': False,
            'image': 'docker-test-image',
            'port': None,
            'params': {
                'ports': {
                    80: 80
                },
                'stdin_open': True,
                'tty': True,
                'command': '/bin/sleep 30'
            }
        }

        ctx = MockCloudifyContext(
            node_id=test_node_id,
            properties=test_properties
        )

        return ctx

    def test_start_container_clean(self):
        """ This test pulls the docker-dev image from
            the docker hub and deletes it.
        """
        ctx = self.mock_ctx('test_start_container_clean')
        daemon_client = {}
        client = self.get_client(daemon_client)
        repository = 'docker-test-image'

        for stream in client.pull(repository, stream=True):
            streamd = json.loads(stream)
            if streamd.get('status', 'Downloading') is not 'Downloading':
                ctx.logger.info('Pulling Image status: {0}.'.format(
                    streamd['status']))

        arguments = {}
        arguments['name'] = ctx.node.properties.get('resource_id')
        arguments['image'] = ctx.node.properties.get('image')
        for key in ctx.node.properties.get('params').keys():
            arguments[key] = ctx.node.properties['params'][key]

        container = client.create_container(**arguments)

        ctx.node.properties['use_external_resource'] = True
        ctx.node.properties['resource_id'] = container.get('Id')
        ctx.instance.runtime_properties['container_id'] = \
            ctx.node.properties['resource_id']

        now = time.time()
        tasks.start(10, ctx=ctx)

        if time.time() - now < 30:
            self.assertTrue(ctx.instance.runtime_properties['container_id'] in
                            [c.get('Id') for c in client.containers()])
        else:
            self.assertTrue(False)
        client.stop(container.get('Id'))
        client.remove_container(container.get('Id'))
