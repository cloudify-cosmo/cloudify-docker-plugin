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

import os
import unittest
import logging

import docker

from cloudify import exceptions
from cloudify.workflows import local, ctx as workflow_ctx
from cloudify.decorators import workflow, operation
from cloudify import ctx as operation_ctx

from docker_plugin import tasks


_CMD = ('sh -c \'i=0; while [ 1 ]; do i=`expr $i + 1`;'
        '/bin/echo Hello world $i; sleep 1; done\'')

class TestCaseBase(unittest.TestCase):

    def _assert_container_running(self, assert_fun):
        assert_fun(
            self.client.inspect_container(
                self.runtime_properties['container']
            )['State']['Running']
        )

    @property
    def blueprint_dir(self):
        return os.path.abspath(os.path.join(os.path.dirname(__file__),
                                            'blueprint'))

    @property
    def runtime_properties(self):
        return self.env.storage.get_node_instances()[0].runtime_properties

    def _execute(self, operations,
                 container_config=None,
                 docker_env_var=None,
                 custom_operation_kwargs=None,
                 container_start=None,
                 container_remove=None,
                 image_build=None,
                 image_import=None,
                 task_retries=5):
        inputs = dict(
            daemon_client={},
            image_import=image_import or {},
            image_build=image_build or {
                'path': self.blueprint_dir
            },
            container_config=container_config or {},
            container_start=container_start or {},
            container_stop={},
            container_remove=container_remove or {},
            docker_env_var=docker_env_var or {},
            custom_operation_kwargs=custom_operation_kwargs or {},
        )
        blueprint_path = os.path.join(self.blueprint_dir, 'blueprint.yaml')
        if not self.env:
            self.env = local.init_env(blueprint_path,
                                      name=self._testMethodName,
                                      inputs=inputs)
        self.env.execute('execute_operations',
                         parameters={'operations': operations},
                         task_retries=task_retries,
                         task_retry_interval=1)

    def setUp(self):
        self.client = docker.Client()
        self.env = None
        self.original_custom_operation = custom_operation

    def cleanup(self):
        custom_operation = self.original_custom_operation

    def tearDown(self):
        super(TestCaseBase, self).tearDown()
        custom_operation = self.original_custom_operation
        self.delete_container()

    def delete_container(self):
        try:
            self._execute(['delete'],
                          task_retries=0)
        except Exception:
            pass

    def patch_custom_operation(self, new_operation):
        # celery caches tasks so we force use of stub _task
        global custom_operation
        custom_operation = operation(new_operation,
                                     force_not_celery=True)


@workflow
def execute_operations(operations, **kwargs):
    node = next(workflow_ctx.nodes)
    instance = next(node.instances)
    for operation in operations:
        instance.execute_operation('test.{0}'.format(operation)).get()


@operation
def set_docker_env_var(docker_env_var, **kwargs):
    operation_ctx.runtime_properties['docker_env_var'] = docker_env_var


# celery caches tasks so we force use of stub _task
@operation(force_not_celery=True)
def custom_operation(custom_operation_kwargs, **kwargs):
    raise RuntimeError('patched by tests')
