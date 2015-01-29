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
import os

# Third Party Imports
import testtools
from docker import Client
from docker import errors

# Cloudify Imports is imported and used in operations
from cloudify.workflows import local
from cloudify.exceptions import NonRecoverableError

IGNORED_LOCAL_WORKFLOW_MODULES = (
    'worker_installer.tasks',
    'plugin_installer.tasks'
)


class TestPullWorkflow(testtools.TestCase):

    def setUp(self):
        super(TestPullWorkflow, self).setUp()
        # build blueprint path
        blueprint_path = os.path.join(os.path.dirname(__file__),
                                      'blueprint', 'test_pull.yaml')

        inputs = {
            'test_repo': 'docker-test-image',
            'test_tag': 'latest',
            'test_container_name': 'test-container'
        }

        # setup local workflow execution environment
        self.env = local.init_env(
            blueprint_path, name=self._testMethodName, inputs=inputs,
            ignored_modules=IGNORED_LOCAL_WORKFLOW_MODULES)

    def get_client(self, daemon_client):

        try:
            return Client(**daemon_client)
        except errors.DockerException as e:
            raise NonRecoverableError('Error while getting client: '
                                      '{0}.'.format(str(e)))

    def tests_pull_workflow(self):
        """ Tests the install workflow using the built in
            workflows.
        """
        daemon_client = {}
        client = self.get_client(daemon_client)

        for container in client.containers(all=True):
            if 'test-container' in \
                    ''.join([name for name in container.get('Names')]):
                client.remove_container('test-container')

        if ['docker-test-image:latest'] in \
                [i.get('RepoTags') for i in client.images()]:
            client.remove_image('docker-test-image', force=True)

        # execute install workflow
        self.env.execute('install', task_retries=0)

        container_instance = {}

        for instance in self.env.storage.get_node_instances():
            if 'container_id' in instance.runtime_properties.keys():
                container_instance = instance

        container_id = container_instance.runtime_properties.get(
            'container_id')
        containers = client.containers(all=True)
        self.assertTrue(container_id in [c.get('Id') for c in containers])

        self.env.execute('uninstall', task_retries=3)
        repotags = []
        for i in client.images():
            repotags.append(i.get('RepoTags'))

        self.assertFalse('docker-test-image' in [tag for tag in repotags])
        if ['docker-test-image:latest'] in \
                [i.get('RepoTags') for i in client.images()]:
            client.remove_image('docker-test-image', force=True)
