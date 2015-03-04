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

# Cloudify Imports is imported and used in operations
from cloudify.exceptions import NonRecoverableError
from docker_plugin import docker_client


class TestClient(testtools.TestCase):

    def test_bad_daemon_dictionary(self):
        daemon_client = {
            'base_url': 'ZZZZZZXXXXXX'
        }
        ex = self.assertRaises(
            NonRecoverableError, docker_client.get_client, daemon_client)
        self.assertIn('Error while getting client', ex.message)
