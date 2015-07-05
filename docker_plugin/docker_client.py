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


# Third-party Imports
from docker.client import Client
from docker.errors import DockerException

# Cloudify Imports
from cloudify.exceptions import NonRecoverableError


def get_client(daemon_client):
    """Get client.

    Returns docker client using daemon_client as configuration.

    :param daemon_client: optional configuration for client creation
    :raises NonRecoverableError:
        when docker.errors.APIError during client.
    :return: docker client
    """

    try:
        return Client(**daemon_client)
    except DockerException as e:
        raise NonRecoverableError(
            'Error while getting client: {0}.'.format(str(e)))
