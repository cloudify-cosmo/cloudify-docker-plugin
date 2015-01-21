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


"""Cloudify tasks that operate docker containers using python docker api"""

# Built-in Imports
import json

# Third-party Imports
import docker.errors

# Cloudify Imports
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError
from cloudify.decorators import operation
import docker_plugin.docker_wrapper as docker_wrapper


@operation
def pull(daemon_client=None,
         image_pull=None,
         **kwargs):
    """Pull image from the Docker hub.

    :param daemon_client: optional configuration for client creation
    :param image_pull: configuration for pulling the image
    :raises NonRecoverableError:
        when 'repository' in 'image_import' is not specified.

    """

    client = daemon_client or {}
    image_pull = image_pull or {}
    client = docker_wrapper.get_client(daemon_client)

    if image_pull.get('repository', None) is None:
        raise NonRecoverableError('Missing respository name.')

    repository = image_pull.get('repository')
    ctx.logger.info('Pulling image: {0}'.format(repository))

    if image_pull.get('stream', True) is False:
        image_pull['stream'] = True
        ctx.logger.debug('Setting streaming to True even though '
                         'True was not provided in blueprint.')

    for stream in client.pull(**image_pull):
        streamd = json.loads(stream)
        if streamd.get('status', 'Downloading') is not 'Downloading':
            ctx.logger.info('Pulling Image status: {0}.'.format(
                streamd['status']))


@operation
def build(daemon_client=None, image_build=None, **kwargs):
    """ Builds an image.
    """

    daemon_client = daemon_client or {}
    image_build = image_build or {}

    client = docker_wrapper.get_client(daemon_client)

    if image_build.get('path', None) is None:
        raise NonRecoverableError('No path to a Dockerfile was provided.')

    ctx.logger.info('Building image from path {}'.format(image_build['path']))

    try:
        image_stream = client.build(**image_build)
    except OSError as e:
        raise NonRecoverableError('Error while building image: '
                                  '{0}'.format(str(e)))

    image_id = docker_wrapper.get_build_image_id(client, image_stream)

    ctx.logger.info('Build image successful. Image: {0}'.format(image_id))
    ctx.instance.runtime_properties['image'] = image_id


@operation
def import_image(daemon_client=None, image_import=None, **kwargs):
    """ Imports an image.
    """

    daemon_client = daemon_client or {}
    image_import = image_import or {}

    client = docker_wrapper.get_client(daemon_client)

    if image_import.get('src', None) is None:
        raise NonRecoverableError('No source was provided. '
                                  'Import image exiting.')

    ctx.logger.info('Importing image.')

    output = client.import_image(**image_import)

    image_id = docker_wrapper.get_import_image_id(client, output)
    ctx.logger.info('Image import successful. Image: {0}'.format(image_id))
    ctx.instance.runtime_properties['image'] = image_id


@operation
def create_container(container_config,
                     daemon_client=None,
                     **kwargs):
    """Create container using image from ctx.instance.runtime_properties.

    Add variables from ctx.instance.runtime_properties['docker_env_var']
    to variables from "container_config['enviroment']" and
    relayed to container as enviromental variables.

    Create container from image from ctx.instance.runtime_properties
    with options from 'container_config'.
    'command' in 'container_config' must be specified.

    :param daemon_client: optional configuration for client creation
    :param container_config: configuration for creating container
    :raises NonRecoverableError:
        when docker.errors.docker.errors.APIError during start
        (for example when 'command' is not specified in 'container_create').

    """

    container_config = container_config or {}
    daemon_client = daemon_client or {}
    client = docker_wrapper.get_client(daemon_client)

    environment = container_config.get('environment', {})

    for key, value in ctx.instance.runtime_properties.get(
            'docker_env_var', {}).items():
        if key not in environment:
            environment[str(key)] = str(value)

    container_config['environment'] = environment

    ctx.logger.info('Creating container')
    image = docker_wrapper.get_image_or_raise(client, container_config)

    try:
        container = client.create_container(image, **container_config)
    except docker.errors.APIError as e:
        raise NonRecoverableError('Error while creating container: '
                                  '{0}'.format(str(e)))

    ctx.instance.runtime_properties['container'] = container['Id']
    ctx.logger.info('Container created: {0}.'.format(container['Id']))


@operation
def run(container_start=None,
        processes_to_wait_for=None,
        daemon_client=None,
        **kwargs):
    """Run container.

    Run container which id is specified in
    ctx.instance.runtime_properties['container'] with optional options
    from 'container_start'.

    Retreives host IP, forwarded ports and top info about the container
    from the Docker and log it. Additionally sets in
    ctx.instance.runtime_properties:
    -   host_ip (dictionary of strings)
    -   forwarded ports (list)
    -   Docker's networkSettings (dictionary)

    Logs:
         Container id,
         Container ports,
         Container top information

    :param daemon_client: optional configuration for client creation
    :param processes_to_wait_for: a dict containing a list of processes
                                    that are to be waited for (process_names)
                                    and the wait timeout in seconds
                                    (wait_for_time_secs) before checking if
                                    these processes are alive in the
                                    docker container.
                                    Sleep interval is specified by 'interval'
                                    (default: 1 second)
                                    (based on the Container.top() method).
    :param container_start: configuration for starting a container
    :raises NonRecoverableError:
        when 'container' in ctx.instance.runtime_properties is None
        or when docker.errors.docker.errors.APIError during start.

    """
    container_start = container_start or {}
    processes_to_wait_for = processes_to_wait_for or {}
    client = docker_wrapper.get_client(daemon_client)

    docker_wrapper.start_container(client,
                                   processes_to_wait_for,
                                   container_start)

    if ctx.instance.runtime_properties.get('container', None) is None:
        raise NonRecoverableError('No container provided.')

    container = ctx.instance.runtime_properties.get('container')
    ctx.logger.info('Starting container.')

    try:
        client.start(container, **container_start)
    except docker.errors.APIError as e:
        raise NonRecoverableError('Failed to start container: '
                                  '{0}.'.format(str(e)))

    docker_wrapper.to_wait_for_processes(client, container,
                                         processes_to_wait_for)

    ctx.logger.info('Started container: {0}.'.format(container))

    container = docker_wrapper.get_container_info(client)
    container_inspect = docker_wrapper.inspect_container(client)
    ctx.instance.runtime_properties['ports'] = container['Ports']
    ctx.instance.runtime_properties['network_settings'] = \
        container_inspect['NetworkSettings']
    ctx.logger.info('Container: {0}\nForwarded ports: {1}\nTop: {2}.'.format(
        container['Id'], ctx.instance.runtime_properties['ports'],
        docker_wrapper.get_top_info(client)))


@operation
def stop(container_stop=None,
         daemon_client=None,
         **kwargs):
    """Stop container.

    Stop container which id is specified in ctx.instance.runtime_properties
    ['container'] with optional options from 'container_stop'.


    :param daemon_client: optional configuration for client creation
    :param container_stop: configuration for stopping a container
    :raises NonRecoverableError:
        when 'container' in ctx.instance.runtime_properties is None
        or when docker.errors.docker.errors.APIError during stop.

    """
    container_stop = container_stop or {}
    daemon_client = daemon_client or {}
    client = docker_wrapper.get_client(daemon_client)

    ctx.logger.info('Stopping container.')
    container = docker_wrapper.get_container_or_raise(client)

    try:
        client.stop(container, **container_stop)
    except docker.errors.APIError as e:
        raise NonRecoverableError('Failed to stop container: '
                                  '{0}'.format(str(e)))

    ctx.logger.info('Stopped container.')


@operation
def rm(container_remove=None,
       container_stop=None,
       daemon_client=None,
       **kwargs):
    """Delete container.

    Remove container which id is specified in ctx.instance.runtime_properties
    ['container'] with optional options from 'container_remove'.

    If container is running stop it.
    if "container_remove['remove_image']" is True then remove image.

    :param daemon_client: optional configuration for client creation
    :param container_remove: coniguration for removing container
    :param container_stop: coniguration for stopping a container in case it
                             is running before removal
    :raises NonRecoverableError:
        when 'container' in ctx.instance.runtime_properties is None
        or 'remove_image' in 'container_remove' is True
        and 'image' in ctx.instance.runtime_properties is None
        or when docker.errors.APIError during stop, remove_container,
        remove_image (for example if image is used by another container).

    """
    daemon_client = daemon_client or {}
    client = docker_wrapper.get_client(daemon_client)
    container_info = docker_wrapper.inspect_container(client)

    if container_info and container_info['State']['Running']:
        container = docker_wrapper.get_container_or_raise(client)
        ctx.logger.info('Removing container {}'.format(container))
        try:
            client.remove_container(container, **container_remove)
        except docker.errors.APIError as e:
            raise NonRecoverableError('Failed to delete container: {0}.'
                                      .format(str(e)))

        ctx.logger.info('Removed container {}'.format(container))

    remove_image = docker_wrapper.container_remove.pop('remove_image', None)
    docker_wrapper.remove_container(client, container_remove)
    if remove_image:
        docker_wrapper.remove_image(client)
