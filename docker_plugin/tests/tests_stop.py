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

# Third Party Imports
import testtools
from docker import Client
from docker import errors

# Cloudify Imports is imported and used in operations
from docker_plugin import tasks
from cloudify.mocks import MockCloudifyContext
from cloudify.exceptions import NonRecoverableError


class TestStop(testtools.TestCase):

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
            'name': 'cloudify-test-container',
            'use_external_resource': False,
            'image': 'docker-test-image',
            'port': None,
            'params': {
                'ports': {
                    80: 80
                },
                'stdin_open': True,
                'tty': True,
                'command': '/bin/sleep 60'
            }
        }

        ctx = MockCloudifyContext(
            node_id=test_node_id,
            properties=test_properties
        )

        return ctx

    def test_stop_clean(self):
        """ This test pulls the docker-dev image from
            the docker hub and deletes it.
        """
        ctx = self.mock_ctx('test_stop_clean')
        daemon_client = {}
        client = self.get_client(daemon_client)

        arguments = {}
        arguments['name'] = ctx.node.properties.get('name')
        arguments['image'] = ctx.node.properties.get('image')
        for key in ctx.node.properties.get('params').keys():
            arguments[key] = ctx.node.properties['params'][key]

        container = client.create_container(**arguments)

        ctx.node.properties['use_external_resource'] = True
        ctx.node.properties['name'] = container.get('Id')
        ctx.instance.runtime_properties['container_id'] = \
            container.get('Id')

        d = {}
        d['container'] = container.get('Id')

        client.start(**d)

        tasks.stop(10, 20, ctx=ctx)

        self.assertTrue(
            container.get('Id') in
            [c.get('Id') for c in client.containers(all=True)] and
            container.get('Id') not in
            [c.get('Id') for c in client.containers()])

        client.remove_container(container.get('Id'))
