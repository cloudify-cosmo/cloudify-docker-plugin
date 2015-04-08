# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
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

import os
import testtools

from fabric.api import settings, run
from fabric.api import env as fabric_env
from cloudify.workflows import local

TEST_KEY_NAME = 'docker_test_key'
TEST_KEY_PATH = '~/.ssh/docker_test_key.pem'
IGNORED_LOCAL_WORKFLOW_MODULES = (
    'worker_installer.tasks',
    'plugin_installer.tasks'
)


class DockerPluginTests(testtools.TestCase):

    def setUp(self):
        super(DockerPluginTests, self).setUp()

        self.blueprint_path = \
            os.path.join(os.path.dirname(__file__),
                         'resources', 'blueprint.yaml')

        inputs = {
            'aws_access_key_id': None,
            'aws_secret_access_key': None,
            'current_ip': '0.0.0.0/0',
            'image': 'ami-3cf8b154',
            'size': 'm3.medium',
            'key_name': TEST_KEY_NAME,
            'private_key_path': TEST_KEY_PATH,
            'core_version': '3.2m8',
            'plugins_version': '1.2m8',
            'agent_user': 'ubuntu'
        }

        self.env = local.init_env(
            self.blueprint_path, name=self._testMethodName,
            inputs=inputs,
            ignored_modules=IGNORED_LOCAL_WORKFLOW_MODULES)

    def tearDown(self):
        super(DockerPluginTests, self).tearDown()
        self.env.execute('uninstall', task_retries=10)

    def test_plugin(self):

        self.env.execute('install', task_retries=10)

        for node in self.env.storage.get_nodes():
            if 'docker_system_test_key_pair' in node.id:
               keypair = node

        for node_instance in self.env.storage.get_node_instances():
            if 'docker_system_test_host' in node_instance.node_id:
                host = node_instance

        if not keypair or not host:
            raise Exception(
                'Keypair {0} or host {0} cannot be None.'
                .format(keypair, host))

        fabric_env = {
            'user': 'ubuntu',
            'key_filename': keypair.properties['private_key_path'],
            'host_string': host.runtime_properties['public_ip_address']
        }

        command = 'nosetests --with-cov --cov-report term-missing ' \
                  '--cov docker_system_test/docker_plugin ' \
                  'docker_system_test/docker_plugin/tests'

        with settings(**fabric_env):
            result = run(command)

        self.assertIn('OK', result)
