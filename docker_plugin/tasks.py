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
from utils import build_arg_dict
from utils import get_container_info
from utils import inspect_container
from docker_plugin import docker_client
import docker_plugin.docker_wrapper as docker_wrapper


@operation
def pull(daemon_client=None, **_):
    """Pull image from the Docker hub.

    :param daemon_client: optional configuration for client creation

    """

    daemon_client = daemon_client or {}
    client = docker_client.get_client(daemon_client)

    if ctx.node.properties['use_external_resource'] is True:
        ctx.instance.runtime_properties['repository'] = \
            ctx.node.properties['resource_id']
        return

    arguments = dict()
    args_to_merge = build_arg_dict(ctx.node.properties['params'].copy(), {})
    arguments.update(args_to_merge)
    arguments['repository'] = ctx.node.properties['resource_id']

    ctx.logger.info('Pulling repository/image: {0}'.format(
        arguments))

    try:
        for stream in client.pull(**arguments):
            streamd = json.loads(stream)
            if streamd.get('status', 'Downloading') is not 'Downloading':
                ctx.logger.info('Pulling Image status: {0}.'.format(
                    streamd['status']))
    except docker.errors.APIError as e:
        raise NonRecoverableError('Unabled to pull image: {0}.'
                                  'Error: {1}.'.format(
                                      ctx.node.properties['resource_id'],
                                      str(e)))

    ctx.instance.runtime_properties['image_id'] = arguments['repository']


@operation
def build(daemon_client=None, **_):
    """ Builds an image.
    :param daemon_client: optional configuration for client creation
    """

    daemon_client = daemon_client or {}
    client = docker_client.get_client(daemon_client)

    arguments = dict()
    args_to_merge = build_arg_dict(ctx.node.properties['params'].copy(), {})
    arguments.update(args_to_merge)
    arguments['tag'] = ctx.node.properties['resource_id']

    ctx.logger.info('Building image from blueprint: ')

    try:
        response = [line for line in client.build(**arguments)]
    except docker.errors.APIError as e:
        raise NonRecoverableError('Error while building image: '
                                  '{0}.'.format(
                                      ctx.node.properties['resource_id'],
                                      str(e)))
    except OSError as e:
        raise NonRecoverableError('Error while building image: '
                                  '{0}'.format(str(e)))

    ctx.logger.debug('Response: {}'.format(response))
    ctx.instance.runtime_properties['image_id'] = \
        ctx.node.properties['resource_id']
    ctx.logger.info('Build image successful. Image: {0}'.format(
        ctx.node.properties['resource_id']))


@operation
def import_image(daemon_client=None, **_):
    """ Imports an image.
    :param daemon_client: optional configuration for client creation
    """

    daemon_client = daemon_client or {}
    client = docker_client.get_client(daemon_client)
    arguments = dict()
    args_to_merge = build_arg_dict(ctx.node.properties['params'].copy(), {})
    arguments.update(args_to_merge)
    arguments['tag'] = ctx.node.properties['resource_id']
    arguments['src'] = ctx.node.properties['src']

    ctx.logger.info('Importing image from blueprint.')

    output = client.import_image(**arguments)

    ctx.logger.info('output: {}'.format(output))

    image_id = docker_wrapper.get_import_image_id(client, output)
    ctx.logger.info('Image import successful. Image: {0}'.format(image_id))
    ctx.instance.runtime_properties['image_id'] = image_id


@operation
def create_container(daemon_client=None, **_):
    """Create container using image from ctx.instance.runtime_properties.
    :param daemon_client: optional configuration for client creation
    """

    daemon_client = daemon_client or {}
    client = docker_client.get_client(daemon_client)

    arguments = dict()
    args_to_merge = build_arg_dict(ctx.node.properties['params'].copy(), {})
    arguments.update(args_to_merge)
    arguments['name'] = ctx.node.properties['resource_id']
    arguments['image'] = ctx.node.properties['image']

    if ctx.node.properties.get('ports', None) is not None:
        arguments['ports']
        for key in ctx.node.properties['ports'].keys():
            arguments['ports'] = ctx.node.properties['ports'].get(key, None)

    ctx.logger.info('Creating container')

    try:
        container = client.create_container(**arguments)
    except docker.errors.APIError as e:
        raise NonRecoverableError('Error while creating container: '
                                  '{0}'.format(str(e)))

    ctx.instance.runtime_properties['container_id'] = container.get('Id')
    ctx.logger.info('Container created: {0}.'.format(container.get('Id')))


@operation
def run(daemon_client=None, **_):
    """Run container.
    :param daemon_client: optional configuration for client creation
    """

    client = docker_client.get_client(daemon_client)

    arguments = dict()
    args_to_merge = build_arg_dict(ctx.node.properties['params'].copy(), {})
    arguments.update(args_to_merge)
    arguments['container'] = \
        ctx.instance.runtime_properties['docker_container']

    if ctx.node.properties.key('resource_id', None) is not None:
        arguments['container'] = ctx.node.properties['resource_id']
    elif ctx.instance.runtime_properties.get('docker_container',
                                             None) is not None:
        arguments['container'] = \
            ctx.instance.runtime_properties['docker_container']
    else:
        raise NonRecoverableError('No container provided.')

    container = ctx.instance.runtime_properties.get('container')
    ctx.logger.info('Starting container.')

    try:
        client.start(**arguments)
    except docker.errors.APIError as e:
        raise NonRecoverableError('Failed to start container: '
                                  '{0}.'.format(str(e)))

    docker_wrapper.to_wait_for_processes(client, container,
                                         processes_to_wait_for)

    ctx.logger.info('Started container: {0}.'.format(container))

    container = get_container_info(client)
    container_inspect = inspect_container(client)
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
    client = docker_client.get_client(daemon_client)

    ctx.logger.info('Stopping container.')
    container = docker_wrapper.get_container_or_raise(client)

    try:
        client.stop(container, **container_stop)
    except docker.errors.APIError as e:
        raise NonRecoverableError('Failed to stop container: '
                                  '{0}'.format(str(e)))

    ctx.logger.info('Stopped container.')


@operation
def remove_container(container_remove=None,
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
    client = docker_client.get_client(daemon_client)
    container_info = inspect_container(client)

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
