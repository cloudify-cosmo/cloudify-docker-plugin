########
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

from cosmo_tester.framework.testenv import TestCase

TEST_KEY_NAME = 'docker_test_key'
TEST_KEY_PATH = '~/.ssh/docker_test_key.pem'


class DockerPluginTests(TestCase):

    def setUp(self):
        super(DockerPluginTests, self).setUp()

    def _set_up(self):
        self.blueprint_path = 'resources/blueprint.yaml'

        inputs = {
            'aws_access_key_id': self.env.aws_access_key_id,
            'aws_secret_access_key': self.env.aws_secret_access_key,
            'current_ip': self._get_current_machine_ip(),
            'image': self.env.ubuntu_image_name,
            'size': self.env.medium_instance_type,
            'key_name': TEST_KEY_NAME,
            'private_key_path': TEST_KEY_PATH
        }

    def _run_local_install_workflow(self):
        pass

    def _run_local_uninstall_workflow(self):
        pass

    def _install_virtual_env_remotely(self, elastic_ip):
        pass

    def _install_docker_plugin_remotely(self, elastic_ip):
        pass

    def _run_nosetests_remotely(self, elastic_ip, path_to_tests_directory):
        pass

    def _get_current_machine_ip(self):
        pass
