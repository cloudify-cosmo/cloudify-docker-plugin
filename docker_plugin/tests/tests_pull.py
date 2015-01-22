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
import testtools

# Third Party Imports
from docker import Client
from docker import errors

# Cloudify Imports is imported and used in operations
from docker_plugin import tasks
from cloudify.mocks import MockCloudifyContext
from cloudify.exceptions import NonRecoverableError


class TestPull(testtools.TestCase):

    def get_client(self):
        try:
            return Client(base_url='unix://var/run/docker.sock')
        except errors.DockerException as e:
            raise NonRecoverableError(
                'Error while getting client: {0}.'.format(str(e)))

    def mock_ctx(self, test_name):
        """ Creates a mock context for the instance
            tests
        """

        test_node_id = test_name
        test_properties = {
            'resource_id': 'docker-dev',
            'use_external_resource': False,
            'tag': None,
            'params': {
            }
        }

        ctx = MockCloudifyContext(
            node_id=test_node_id,
            properties=test_properties
        )

        return ctx

    def test_pull_clean(self):
        """ This test pulls the docker-dev image from
            the docker hub and deletes it.
        """

        ctx = self.mock_ctx('test_pull_clean')
        client = self.get_client()

        tasks.pull(ctx=ctx)
        image_id = ctx.instance.runtime_properties['image_id']
        if client.images(name=image_id) is not None:
            test_passed = True
            client.remove_image(image_id)
        self.AssertTrue(test_passed)