# coding=utf-8
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


'''A simple system test that creates a Docker container in Cloudify with a port
exposed and tests connectivity.'''


import logging
import socket

from tests.SystemTestBase import SystemTestBase


_BLUEPRINT = 'tests/system_test_networking_blueprint.yaml'
_PORT = 1000


class TestPluginNetworking(SystemTestBase):

    def setUp(self):
        self.blueprint_path = _BLUEPRINT
        super(TestPluginNetworking, self).setUp()

    def runTest(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logging.info(
            'Connecting to {}:{}...'.format(
                self.cfy_helper.get_management_ip(),
                _PORT
            )
        )
        try:
            sock.connect((self.cfy_helper.get_management_ip(), _PORT))
        except socket.error as e:
            logging.error('error: {}'.format(str(e)))
            raise AssertionError(e)
        else:
            logging.info('Socket connect succeeded')
            sock.close()
