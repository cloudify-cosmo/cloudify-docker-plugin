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


'''A wrapper test case class for simple Cloudify system tests.'''


from __future__ import print_function

import datetime
import os
import random
import string
import sys
import unittest

from cosmo_tester.framework.cfy_helper import CfyHelper
from cosmo_tester.framework.testenv import CLOUDIFY_TEST_MANAGEMENT_IP


class SystemTestBase(unittest.TestCase):

    def __init__(self, test_function_name):
        try:
            management_ip = os.environ[CLOUDIFY_TEST_MANAGEMENT_IP]
        except KeyError:
            print(
                ('`{}\' environment variable must be set in order to execute'
                ' this test.'.format(CLOUDIFY_TEST_MANAGEMENT_IP)),
                file=sys.stderr
            )
            raise
        self.blueprint_path = None
        self.deployments = []
        super(SystemTestBase, self).__init__(test_function_name)
        self.cfy_helper = CfyHelper('.', management_ip)

    def setUp(self):
        super(SystemTestBase, self).setUp()
        if self.blueprint_path is not None:
            blueprint_id = self._generate_id('blueprint')
            deployment_id = self._generate_id('deployment')
            self.cfy_helper.upload_blueprint(
                blueprint_id,
                self.blueprint_path,
                True
            )
            self.cfy_helper.create_deployment(
                blueprint_id,
                deployment_id,
                True
            )
            self.cfy_helper.execute_install(deployment_id)
            self.deployments.append(deployment_id)

    def tearDown(self):
        for deployment_id in self.deployments:
            self.cfy_helper.execute_uninstall(deployment_id)
        self.deployments = []
        super(SystemTestBase, self).tearDown()

    def _generate_id(self,
        prefix,
        separator1='_',
        separator2='_',
        separator3='_',
        suffix = 'test'
    ):
        return '{}{}{}{}{}{}{}'.format(
            prefix,
            separator1,
            datetime.datetime.now().strftime('%y%m%d%H%M%S%f')[:-4],
            separator2,
            ''.join(random.choice(string.letters) for i in range(10)),
            separator3,
            suffix
        )
