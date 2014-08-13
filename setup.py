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


import setuptools
from setuptools.command.install import install

import docker_plugin
import docker_installation.apt_get_wrapper


LICENCE = open('LICENSE').read()
README = open('README.md').read()
REQUIREMENTS = open('requirements.txt').read().split('\n')


class CustomInstallCommand(install):
    def run(self):
        docker_installation.apt_get_wrapper.install_docker()
        install.run(self)


setuptools.setup(
    author='Michał Soczewka',
    author_email='michal.soczewka@codilime.com',
    name=docker_plugin.__name__,
    version=docker_plugin.__version__,
    description=docker_plugin.__doc__,
    license=LICENCE,
    long_description=README,
    install_requires=REQUIREMENTS,
    packages=['docker_plugin'],
    zip_safe=False,
    cmdclass={'install': CustomInstallCommand}
)
