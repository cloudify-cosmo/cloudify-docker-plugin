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


APACHE_2_LICENSE = \
    '''Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

         http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.'''
DESCRIPTION = (
    'A tiny plugin that injects required runtime properties into the Cloudify'
    ' context needed in the Nodecellar application on Docker example.'
)


setuptools.setup(
    name='properties-injector-plugin',
    author='Michał Soczewka',
    author_email='michal.soczewka@codilime.com',
    version='0.9a',
    license=APACHE_2_LICENSE,
    description=DESCRIPTION,
    packages=setuptools.find_packages(),
    install_requires=['cloudify-plugins-common'],
    zip_safe=True
)
