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

import docker


os.chdir(os.path.dirname(os.path.abspath(__file__)))

LICENCE = open('LICENSE').read()
README = open('README.md').read()
REQUIREMENTS = open('requirements.txt').read().split('\n')

setuptools.setup(name='cloudify-docker-plugin',
                 author='Michał Soczewka',
                 author_email='michal.soczewka@codilime.com',
                 version=docker.__version__,
                 description=docker.__doc__,
                 license=LICENCE,
                 long_description=README,
                 packages=['docker'],
                 install_requires=REQUIREMENTS,
                 zip_safe=False)
