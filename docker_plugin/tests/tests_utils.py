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
import json

# Third Party Imports
import docker

# Cloudify Imports is imported and used in operations
from cloudify.mocks import MockCloudifyContext
from cloudify.exceptions import NonRecoverableError
from docker_plugin import utils


class TestUtils(testtools.TestCase):

    def setUp(self):
        super(TestUtils, self).setUp()
        docker_client = self.get_docker_client()
        self.pull_test_image(docker_client)

    def get_mock_context(self, test_name):

        test_node_id = test_name
        test_properties = {
            'name': test_name,
            'image': {
                'repository': 'docker-test-image'
            }
        }

        ctx = MockCloudifyContext(
            node_id=test_node_id,
            properties=test_properties
        )

        return ctx

    def get_bad_image_id(self):
        return 'z0000000z000z0zzzzz0zzzz000000' \
               '0000zzzzz0zzz00000z0zz0000000000zz'

    def get_docker_client(self):
        return docker.Client()

    def pull_test_image(self, docker_client):
        output = []
        for line in docker_client.pull('docker-test-image', stream=True):
            output.append(json.dumps(json.loads(line)))
        return output

    def get_list_of_docker_image_ids(self, docker_client):
        return [image.get('Id') for image in self.docker_client().images()]

    def get_docker_image(self, docker_client):
        return [image for image in self.docker_client().images()]

    def get_tags_for_docker_image(self, image):
        return [tag for tag in image.get('RepoTags')]

    def get_id_from_image(self, image):
        return image.get('Id')

    def test_get_image_id(self):
        image_id = self.get_bad_image_id()
        tag = 'latest'
        client = self.get_docker_client()
        ex = self.assertRaises(
            NonRecoverableError, utils.get_image_id, tag, image_id, client)
        self.assertIn(
            'Unable to verify', ex.message)
