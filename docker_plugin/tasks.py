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
from docker_plugin import utils
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
            ctx.node.properties.get('resource_id')
        return

    arguments = dict()
    args_to_merge = utils.build_arg_dict(
        ctx.node.properties['params'].copy(), {})
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
    args_to_merge = utils.build_arg_dict(
        ctx.node.properties['params'].copy(), {})
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
    args_to_merge = utils.build_arg_dict(
        ctx.node.properties['params'].copy(), {})
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

    if ctx.node.properties.get('use_external_resource', False):
        if 'resource_id' not in ctx.node.properties.keys():
            raise NonRecoverableError('Use external resource, but '
                                      'no resource id provided.')
        ctx.instance.runtime_properties['container_id'] = \
            ctx.node.properties.get('resource_id')
        if not ctx.instance.runtime_properties.get('container_id') in \
                [c.get('Id') for c in client.containers(all=True)]:
            raise NonRecoverableError('Container specified in resource_id '
                                      'does not exist.')
        return

    arguments = dict()
    arguments = utils.get_create_container_params(ctx=ctx)
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
def start(retry_interval, daemon_client=None, **_):
    """Run container.
    :param daemon_client: optional configuration for client creation
    """

    daemon_client = daemon_client or {}
    client = docker_client.get_client(daemon_client)

    if ctx.node.properties.get('use_external_resource', False):
        if 'resource_id' not in ctx.node.properties.keys():
            raise NonRecoverableError('Use external resource, but '
                                      'no resource id provided.')
        if ctx.node.properties.get('resource_id') not in \
                ctx.instance.runtime_properties.get('container_id'):
            ctx.logger.error('The resource_id and container_id do not match. '
                             'Continuing anyway.')
        if ctx.instance.runtime_properties.get('container_id') not in \
                [c.get('Id') for c in client.containers(all=True)]:
            raise NonRecoverableError('{} does not exist.'.format(
                ctx.instance.runtime_properties.get('container_id')))

    arguments = dict()
    arguments = utils.get_start_params(ctx=ctx)
    arguments['container'] = \
        ctx.instance.runtime_properties.get('container_id')

    ctx.logger.info('Starting container.')

    try:
        response = client.start(**arguments)
    except docker.errors.APIError as e:
        raise NonRecoverableError('Failed to start container: '
                                  '{0}.'.format(str(e)))

    ctx.logger.info('Container started: {}.'.format(response))

    if ctx.node.properties.get('params').get('processes_to_wait_for', False):
        utils.wait_for_processes(retry_interval, client, ctx=ctx)

    ctx.logger.info('Started container: {0}.'.format(
        ctx.instance.runtime_properties.get('container_id')))

    if utils.get_container_info(client) is not None:
        inspect_output = utils.inspect_container(client)
        ctx.instance.runtime_properties['ports'] = \
            inspect_output.get('Ports', None)
        ctx.instance.runtime_properties['network_settings'] = \
            inspect_output.get('NetworkSettings', None)

    ctx.logger.info('Container: {0} Forwarded ports: {1} Top: {2}.'.format(
        ctx.instance.runtime_properties.get('container_id'),
        ctx.instance.runtime_properties.get('ports'),
        utils.get_top_info(client)))


@operation
def stop(timeout,
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

    daemon_client = daemon_client or {}
    client = docker_client.get_client(daemon_client)

    container = ctx.instance.runtime_properties.get('container_id')

    ctx.logger.info('Stopping container.')

    try:
        client.stop(container, timeout)
    except docker.errors.APIError as e:
        raise NonRecoverableError('Failed to stop container: '
                                  '{0}'.format(str(e)))

    ctx.logger.info('Stopped container.')


@operation
def remove_container(v, link, force,
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

    container = ctx.instance.runtime_properties.get('container_id')

    ctx.logger.info('Removing container {}'.format(container))

    try:
        client.remove_container(container, v, link, force)
    except docker.errors.APIError as e:
        raise NonRecoverableError('Failed to delete container: {0}.'
                                  .format(str(e)))
    finally:
        ctx.instance.runtime_properties.pop('container_id')

    ctx.logger.info('Removed container {}'.format(container))


@operation
def remove_image(force, noprune, daemon_client=None,
                 **_):

    daemon_client = daemon_client or {}
    client = docker_client.get_client(daemon_client)

    image = ctx.instance.runtime_properties.get('image_id')
    ctx.logger.info('Removing image: {}'.format(image))

    try:
        client.remove_image(image, force, noprune)
    except docker.errors.APIError as e:
        raise NonRecoverableError('Failed to delete image: {0}.'
                                  .format(str(e)))
    finally:
        ctx.instance.runtime_properties.pop('image_id')

    ctx.logger.info('Removed image: {}'.format(image))
