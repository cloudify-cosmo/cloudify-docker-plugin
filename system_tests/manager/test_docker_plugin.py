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
from cosmo_tester.framework.testenv import TestCase

IGNORED_LOCAL_WORKFLOW_MODULES = (
    'worker_installer.tasks',
    'plugin_installer.tasks'
)


class TestDockerPlugin(TestCase):

    def setUp(self):
        super(TestDockerPlugin, self).setUp()

        self.blueprint_path = \
            os.path.join(os.path.dirname(__file__),
                         'resources', 'blueprint.yaml')

        inputs = {
            'current_ip': '0.0.0.0/0',
            'external_network_name': self.external_network_name,
            'image_id': self.env.ubuntu_trusty_image_id,
            'flavor_id': self.env.small_flavor_id,
            'key_name': self.docker_host_key_name,
            'private_key_path': self.docker_host_key_path,
            'core_branch': self.core_branch,
            'plugins_branch': self.plugins_branch,
            'docker_plugin_branch': self.docker_plugin_branch,
            'agent_user': 'ubuntu',
            'openstack_config': {
                'username': self.keystone_username,
                'password': self.keystone_password,
                'tenant_name': self.keystone_tenant_name,
                'auth_url': self.keystone_url
            }
        }

        self.env = local.init_env(
            self.blueprint_path, name=self._testMethodName,
            inputs=inputs,
            ignored_modules=IGNORED_LOCAL_WORKFLOW_MODULES)

    def tearDown(self):
        super(TestDockerPlugin, self).tearDown()
        self.env.execute('uninstall', task_retries=10)

    def test_plugin(self):

        self.env.execute('install', task_retries=10)

        keypair = {}
        host = {}

        for node in self.env.storage.get_nodes():
            if 'docker_system_test_keypair' in node.id:
               keypair = node

        for node_instance in self.env.storage.get_node_instances():
            if 'docker_system_test_floating_ip' in node_instance.node_id:
                host = node_instance

        if not keypair or not host:
            raise Exception(
                'Keypair {0} or host {0} cannot be None.'
                .format(keypair, host))

        fabric_env = {
            'user': 'ubuntu',
            'key_filename': keypair.properties['private_key_path'],
            'host_string': host.runtime_properties['floating_ip_address']
        }

        command = 'source cloudify_system_test/bin/activate && ' \
                  'nosetests --with-cov --cov-report term-missing ' \
                  '--cov docker_system_test/docker_plugin ' \
                  'docker_system_test/docker_plugin/tests'

        with settings(**fabric_env):
            result = run(command)

        self.assertIn('OK', result)

    @property
    def core_branch(self):
        return 'master'

    @property
    def plugins_branch(self):
        return 'master'

    @property
    def docker_plugin_branch(self):
        return self.plugins_branch

    @property
    def docker_host_key_name(self):
        return 'docker_system_test_key'

    @property
    def docker_host_key_path(self):
        return '~/.ssh/docker_system_test_key.pem'

    @property
    def keystone_username(self):
        return 'trammell'

    @property
    def keystone_password(self):
        return '25YJev6563P73Qh'

    @property
    def keystone_tenant_name(self):
        return 'product'

    @property
    def keystone_url(self):
        return 'http://192.168.9.161:5000/v2.0'

    @property
    def external_network_name(self):
        return 'public'
