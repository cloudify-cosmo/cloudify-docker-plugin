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


from setuptools import setup

setup(

    name='cloudify-docker-plugin',
    version='2.0.0',
    author='Cloudify Platform LTD',
    author_email='hello@cloudify.co',
    description='Manage Docker nodes/containers by Cloudify.',
    packages=['cloudify_docker'],
    license='LICENSE',
    zip_safe=False,
    install_requires=[
        "cloudify-common>=4.5.5",
        "docker-py",
        "cloudify-utilities-plugins-sdk==0.0.19",  # Shared Resource Downloader
        "Fabric==1.13.1" # to copy files to docker machine
    ],
    test_requires=[
        "cloudify-common>=4.5.5",
        "docker-py",
        "nose",
    ]
)
