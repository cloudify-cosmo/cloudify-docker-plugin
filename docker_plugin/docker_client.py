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
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError


def get_client(connection_credentials):
    """Get client.

    Returns docker client using daemon_client as configuration.

    :param connection_credentials: optional configuration for client creation
            consists of:
            base_url (str): Refers to the protocol+hostname+port
                            where the Docker server is hosted.
            version (str): The version of the API the client will use.
                           Specify 'auto' to use the API version
                           provided by the server.
            timeout (int): The HTTP request timeout, in seconds.
            tls
    :raises NonRecoverableError:
        when docker.errors.APIError during client.
    :return: docker client
    """
    ctx.logger.info("Creating Docker connection using connection "
                    "credentials: {0}".format(str(connection_credentials)))
    base_url = connection_credentials.get('base_url')
    version = str(connection_credentials.get('version'))
    timeout = int(connection_credentials.get('timeout'))
    tls = True if str(connection_credentials.get(
        'tls')).startswith("true") else False
    try:
        return Client(base_url=base_url,
                      version=version,
                      timeout=timeout,
                      tls=tls)
    except DockerException as e:
        raise NonRecoverableError(
            'Error while getting client: {0}.'.format(str(e)))
