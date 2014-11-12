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
import setuptools
from setuptools.command.install import install

import docker_installation.apt_get_wrapper


class CustomInstallCommand(install):
    def run(self):
        docker_installation.apt_get_wrapper.install_docker()
        install.run(self)


additional_configuration = {}
if 'CELERY_WORK_DIR' in os.environ:
    additional_configuration.update(
        {'cmdclass': {'install': CustomInstallCommand}})

setuptools.setup(
    name='cloudify-docker-plugin',
    version='1.1rc2',
    author='Gigaspaces',
    author_email='cosmo-admin@gigaspaces.com',
    description='A Cloudify plugin enabling it to create'
                'and manipulate Docker containers.',
    license='LICENCE',
    install_requires=[
        'cloudify-plugins-common==3.1rc2',
        'docker-py==0.4.0',
    ],
    packages=['docker_plugin'],
    zip_safe=False,
    **additional_configuration
)
