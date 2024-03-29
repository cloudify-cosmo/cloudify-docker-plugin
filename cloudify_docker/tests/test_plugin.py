########
# Copyright (c) 2014-2020 GigaSpaces Technologies Ltd. All rights reserved
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
import mock
import unittest

from os import (path, mkdir)
from uuid import uuid1

from cloudify.state import current_ctx
# from cloudify.test_utils import workflow_test
from cloudify.mocks import MockCloudifyContext

from cloudify_docker.tasks import (build_image,
                                   list_images,
                                   remove_image,
                                   list_containers,
                                   list_host_details,
                                   find_host_script_path,
                                   remove_container_files,
                                   prepare_container_files)


class TestPlugin(unittest.TestCase):

    def setUp(self):
        super(TestPlugin, self).setUp()

    def get_client_conf_props(self):
        return {
            "client_config": {
                "docker_host": "127.0.0.1",
                "docker_rest_port": "2375"
            }
        }

    def mock_ctx(self,
                 test_name,
                 test_properties,
                 test_runtime_properties=None):
        test_node_id = uuid1()
        ctx = MockCloudifyContext(
                node_id=test_node_id,
                properties=test_properties,
                runtime_properties=test_runtime_properties,
        )
        return ctx

    def test_list_images(self):
        ctx = self.mock_ctx('test_list_images', self.get_client_conf_props())
        current_ctx.set(ctx=ctx)

        images = {
            "Image1": {
                "Created": 1586389397,
                "Id": "sha256:ef5bbc24923e"
            }
        }

        mock_images_list = mock.Mock()
        mock_images_list.images.list.return_value = images
        mock_client = mock.MagicMock(return_value=mock_images_list)

        with mock.patch('docker.DockerClient', mock_client):
            kwargs = {
                'ctx': ctx
            }
            list_images(**kwargs)
            self.assertEqual(ctx.instance.runtime_properties['images'],
                             images)

    def test_list_host_details(self):
        ctx = self.mock_ctx('test_list_host_details',
                            self.get_client_conf_props())
        current_ctx.set(ctx=ctx)

        details = {
            "ID": "PVLH:WS43:SHQI:BBBK:PQKO:N3LP:GKNK:3AHN:DVHD",
            "Containers": 101,
            "ContainersRunning": 0,
            "ContainersPaused": 0,
            "ContainersStopped": 101,
            "Images": 35
        }

        mock_host_details_list = mock.Mock()
        mock_host_details_list.info.return_value = details
        mock_client = mock.MagicMock(return_value=mock_host_details_list)

        with mock.patch('docker.DockerClient', mock_client):
            kwargs = {
                'ctx': ctx
            }
            list_host_details(**kwargs)
            self.assertEqual(ctx.instance.runtime_properties['host_details'],
                             details)

    def test_list_containers(self):
        ctx = self.mock_ctx('test_list_containers',
                            self.get_client_conf_props())
        current_ctx.set(ctx=ctx)

        containers = {
            "Contianer1": {
                "Created": 1586389397,
                "Id": "sha256:e2231923e"
            }
        }

        mock_containers_list = mock.Mock()
        mock_containers_list.containers.list.return_value = containers
        mock_client = mock.MagicMock(return_value=mock_containers_list)

        with mock.patch('docker.DockerClient', mock_client):
            kwargs = {
                'ctx': ctx
            }
            list_containers(**kwargs)
            self.assertEqual(ctx.instance.runtime_properties['contianers'],
                             containers)

    def test_prepare_container_files(self):
        docker_host = "127.0.0.1"
        source = "/tmp/source"
        if not path.exists(source):
            mkdir(source)
        dummy_file_name = str(uuid1())
        dummy_file = path.join(source, dummy_file_name)
        with open(dummy_file, 'w') as outfile:
            outfile.write("dummy stuff")
        destination = "/tmp/destination"
        if not path.exists(destination):
            mkdir(destination)
        resource_config_test = {
            "resource_config": {
                "docker_machine": {
                    "docker_ip": docker_host,
                    "docker_user": "centos",
                    "docker_key": "----RSA----",
                },
                "source": source,
                "destination": destination,
            }
        }

        ctx = self.mock_ctx('test_prepare_container_files',
                            resource_config_test)
        current_ctx.set(ctx=ctx)

        prepare_container_files(ctx)
        self.assertEqual(
            ctx.instance.runtime_properties['destination'], destination)
        self.assertEqual(
            ctx.instance.runtime_properties['docker_host'], docker_host)
        self.assertTrue(path.isfile(path.join(destination, dummy_file_name)))

    def test_remove_container_files(self):
        docker_host = "127.0.0.1"
        source = "/tmp/source"
        destination = "/tmp/destination"
        resource_config_test = {
            "resource_config": {
                "docker_machine": {
                    "docker_ip": docker_host,
                    "docker_user": "centos",
                    "docker_key": "----RSA----",
                },
                "source": source,
                "destination": destination,
            }
        }
        runtime_properties_test = {
            "destination": destination,
        }
        ctx = self.mock_ctx('test_remove_container_files',
                            resource_config_test,
                            runtime_properties_test)
        current_ctx.set(ctx=ctx)

        remove_container_files(ctx)
        self.assertIsNone(
            ctx.instance.runtime_properties.get('destination', None))
        self.assertFalse(path.exists(destination))
        self.assertFalse(path.exists(source))

    def test_build_image(self):
        node_props = self.get_client_conf_props()
        node_props.update({
            "resource_config": {
                "image_content": "FROM amd64/centos:7",
                "tag": "test:1.0"
            }
        })
        build_result = [
            {"stream": "Step 1/1 : FROM amd64/centos:7"},
            {"stream": "\n"},
            {"stream": " ---\u003e 5e35e350aded\n"}
        ]
        build_result_prop = ""
        for chunk in build_result:
            build_result_prop += "{0}\n".format(chunk)

        image_get = [{
            "Created": 1586512602,
            "Labels": {
              "org.label-schema.name": "CentOS Base Image",
              "org.label-schema.schema-version": "1.0",
              "org.label-schema.license": "GPLv2",
              "org.label-schema.build-date": "20191001",
              "org.label-schema.vendor": "CentOS"
            },
            "VirtualSize": 320490159,
            "SharedSize": -1,
            "ParentId": "sha256:683822edc367c7f2d5d5e005fab15e749428efee",
            "Size": 320490159,
            "RepoDigests": None,
            "Id": "sha256:e9abf53b02b1e1fbba06a8ea92c889a2b8de719",
            "Containers": -1,
            "RepoTags": [
              "test:1.0"
            ]
          }
        ]
        ctx = self.mock_ctx('test_build_image', node_props)
        current_ctx.set(ctx=ctx)

        mock_images = mock.Mock()
        mock_images.images.build.return_value = ("Id", iter(build_result))
        mock_images.images.get.return_value = image_get
        mock_client = mock.MagicMock(return_value=mock_images)

        with mock.patch('docker.DockerClient', mock_client):
            kwargs = {
                'ctx': ctx
            }
            build_image(**kwargs)
            self.assertEqual(
                ctx.instance.runtime_properties['build_result'],
                build_result_prop)
            self.assertEqual(
                ctx.instance.runtime_properties['image'],
                repr(image_get))

    def test_remove_image(self):
        node_props = self.get_client_conf_props()
        node_props.update({
            "resource_config": {
                "image_content": "FROM amd64/centos:7",
                "tag": "test:1.0"
            }
        })
        build_result = [{"stream": "Step 1/1 : FROM amd64/centos:7"},
                        {"stream": "\n"},
                        {"stream": " ---\u003e 5e35e350aded\n"}]
        build_result_prop = ""
        for chunk in iter(build_result):
            build_result_prop += "{0}\n".format(chunk)
        runtime_properties_test = {
            "build_result": build_result_prop,
        }

        ctx = self.mock_ctx('test_remove_image',
                            node_props,
                            runtime_properties_test)
        current_ctx.set(ctx=ctx)

        mock_images = mock.Mock()
        mock_images.images.remove = mock.Mock()
        mock_client = mock.MagicMock(return_value=mock_images)

        with mock.patch('docker.DockerClient',
                        mock_client):
            kwargs = {
                'ctx': ctx
            }
            remove_image(**kwargs)
            self.assertIsNone(
                ctx.instance.runtime_properties.get('build_result', None))

    def test_if_volume_mapping_in_script(self):
        containers = {
            "Contianer1": {
                "Created": 1586389397,
                "Id": "sha256:e2231923e"
            }
        }

        mock_containers_get = mock.Mock()
        mock_containers_get.containers.get.return_value = \
            containers['Contianer1']
        mock_client = mock.MagicMock(return_value=mock_containers_get)

        command = 'ansible-playbook -i hosts /uninstall-playbooks/delete.yaml'
        container_args = {
            'volumes_mapping': ['/tmp/tmpfijhaktv', '/tmp/tmpcz0u65ro'],
            'volumes': ['/install-playbooks',
                        '/uninstall-playbooks']
        }
        self.assertEqual(
            find_host_script_path(mock_client, 'sha256:e2231923e',
                                  command, container_args),
            '/tmp/tmpcz0u65ro/delete.yaml')

    def test_if_volume_mapping_not_in_script(self):
        containers = {
            "Contianer1": {
                "Created": 1586389397,
                "Id": "sha256:e2231923e"
            }
        }

        mock_containers_get = mock.Mock()
        mock_containers_get.containers.get.return_value = \
            containers['Contianer1']
        mock_client = mock.MagicMock(return_value=mock_containers_get)

        command = 'ansible-playbook -i hosts /dummy_location/delete.yaml'
        container_args = {
            'volumes_mapping': ['/tmp/tmpfijhaktv', '/tmp/tmpcz0u65ro'],
            'volumes': ['/install-playbooks',
                        '/uninstall-playbooks']
        }
        self.assertIsNone(find_host_script_path(mock_client,
                                                'sha256:e2231923e',
                                                command,
                                                container_args))
