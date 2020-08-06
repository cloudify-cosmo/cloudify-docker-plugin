########
# Copyright (c) 2014-2019 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import pytest

from ecosystem_tests.dorkl import (
    basic_blueprint_test,
    cleanup_on_failure,
    prepare_test,
    blueprints_upload,
    deployments_create,
    executions_start
)


SECRETS_TO_CREATE = {
    'gcp_credentials': True
}

prepare_test(secrets=SECRETS_TO_CREATE)

blueprint_list = ['examples/docker/docker/general/any-container.yaml']
vm = 'examples/blueprint-examples/hello-world-example/gcp.yaml'
docker = 'docker/installation/install-docker.yaml'


@pytest.fixture(scope='function', params=blueprint_list)
def blueprint_examples(request):
    try:
        blueprints_upload(vm, 'vm')
        deployments_create('vm')
        executions_start('install', 'vm')
        blueprints_upload(vm, 'docker')
        deployments_create('docker')
        executions_start('install', 'docker')
        try:
            dirname_param = os.path.dirname(request.param).split('/')[-1:][0]
            basic_blueprint_test(
                request.param,
                dirname_param,
                timeout=3000)
        except BaseException:
            cleanup_on_failure(request.param)
            raise
    except BaseException:
        cleanup_on_failure('vm')


def test_blueprints(blueprint_examples):
    assert blueprint_examples is None
