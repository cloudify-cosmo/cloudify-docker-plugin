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


import os
import re
import pathlib
from setuptools import setup


def get_version():
    current_dir = pathlib.Path(__file__).parent.resolve()
    with open(os.path.join(current_dir, 'cloudify_docker/__version__.py'),
              'r') as outfile:
        var = outfile.read()
        return re.search(r'\d+.\d+.\d+', var).group()


setup(

    name='cloudify-docker-plugin',
    version=get_version(),
    author='Cloudify Platform LTD',
    author_email='hello@cloudify.co',
    description='Manage Docker nodes/containers by Cloudify.',
    packages=['cloudify_docker'],
    license='LICENSE',
    zip_safe=False,
    install_requires=[
        "cloudify-common>=4.5.5",
        "docker>=5.0.3", # Latest with official support for python 3.6 is 5.0.3
        "cloudify-utilities-plugins-sdk>=0.0.61",  # Shared Resource Downloader
        "fabric==2.7.1",
        "patchwork"  # to copy files to docker machine
    ],
    test_requires=[
        "cloudify-common>=4.5.5",
        "docker>=5.0.3",
    ]
)
