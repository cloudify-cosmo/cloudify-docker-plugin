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


def get_client(daemon_client):
    """Get client.

    Returns docker client using daemon_client as configuration.

    :param daemon_client: optional configuration for client creation
    :raises NonRecoverableError:
        when docker.errors.APIError during client.
    :return: docker client
    """

    try:
        ctx.logger.info("Daemom connection options: {0}.".format(
            str(daemon_client)))
        tp = daemon_client.get('transport_protocol', 'tcp')
        docker_host = daemon_client.get('host_string', 'localhost')
        docker_port = daemon_client.get('host_port', 2375)

        base_url = "{0}://{1}:{2}".format(tp, docker_host, docker_port)
        version = str(daemon_client.get('api_version', '1.19'))
        connection_timeout = int(
            daemon_client.get('connection_timeout', 60))
        use_tls = daemon_client.get('enable_tls', False)

        return Client(base_url=base_url,
                      version=version,
                      tls=use_tls,
                      timeout=connection_timeout)

    except DockerException as e:
        raise NonRecoverableError(
            'Error while getting client: {0}.'.format(str(e)))
