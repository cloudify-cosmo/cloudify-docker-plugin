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

import docker_plugin


LICENCE = open('LICENSE').read()
README = open('README.md').read()
REQUIREMENTS = open('requirements.txt').read().split('\n')


setuptools.setup(author='Michał Soczewka',
                 author_email='michal.soczewka@codilime.com',
                 name=docker_plugin.__name__,
                 version=docker_plugin.__version__,
                 description=docker_plugin.__doc__,
                 license=LICENCE,
                 long_description=README,
                 install_requires=REQUIREMENTS,
                 packages=setuptools.find_packages(),
                 zip_safe=False,
                 scripts=['bin/install_docker.sh'])
