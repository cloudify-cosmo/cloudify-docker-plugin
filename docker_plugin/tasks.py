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
from cloudify.exceptions import NonRecoverableError, RecoverableError
from cloudify.decorators import operation
from docker_plugin import utils
from docker_plugin import docker_client


@operation
def pull(daemon_client=None, **_):
    """ cloudify.docker.Image type create lifecycle operation.
        Identical to the docker pull command.

    :node_property repository: The repository to pull.
    :node_property params: (Optional) Use any other parameter allowed
        by the docker API to Docker PY.
    :param daemon_client: optional configuration for client creation
    """

    daemon_client = daemon_client or {}
    client = docker_client.get_client(daemon_client)

    arguments = dict()
    arguments['tag'] = ctx.node.properties['tag']
    arguments['repository'] = ctx.node.properties['repository']
    arguments.update(ctx.node.properties['params'].copy())

    ctx.logger.info('Pulling repository: {0}'.format(
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
                                      arguments,
                                      str(e)))

    image_id = utils.get_newest_image_id(client)
    ctx.instance.runtime_properties['image_id'] = image_id
    ctx.logger.info('Pulled image. Set image_id: {0}'.format(image_id))


@operation
def build(daemon_client=None, **_):
    """ cloudify.docker.BuildImage type create lifecycle operation.
        Derives some definition from parent type cloudify.docker.Image.
        Similar to the docker build command.

    :node_property use_external_resource: True or False. Use existing
        instead of creating a new resource.
    :node_property resource_id:  A tag to add to the final image.
    :node_property params: (Optional) Use any other parameter allowed
        by the docker API to Docker PY. Either path or fileobj needs
        to be set. path can be a local path (to a directory containing
        a Dockerfile) or a remote URL. fileobj must be a readable
        file-like object to a Dockerfile.
    :param daemon_client: optional configuration for client creation
    """

    daemon_client = daemon_client or {}
    client = docker_client.get_client(daemon_client)

    arguments = dict()
    arguments['tag'] = ctx.node.properties['tag']
    arguments.update(ctx.node.properties['params'].copy())

    ctx.logger.info('Building image.')
    ctx.logger.debug('Provided params: {}'.format(arguments))

    try:
        response = [line for line in client.build(**arguments)]
    except docker.errors.APIError as e:
        raise NonRecoverableError('Error while building image: '
                                  '{0}.'.format(
                                      ctx.node.properties['resource_id'],
                                      str(e)))
    except TypeError:
        raise NonRecoverableError('No fileobj or path was provided.')
    except OSError as e:
        raise NonRecoverableError('Error while building image: '
                                  '{0}'.format(str(e)))

    ctx.logger.debug('Response: {}'.format(response))

    image_id = utils.get_newest_image_id(client)
    ctx.instance.runtime_properties['image_id'] = image_id
    ctx.logger.info('Build image successful. Image: {0}'.format(image_id))


@operation
def import_image(daemon_client=None, **_):
    """ cloudify.docker.ImportImage type create lifecycle operation.
        Derives some definition from parent type cloudify.docker.Image.
        Identical to the docker import command.

    :node_property use_external_resource: True or False. Use existing
        instead of creating a new resource.
    :node_property resource_id:  The repository to create.
    :node_property src: Path to tarfile or URL.
    :node_property params: (Optional) Use any other parameter allowed
        by the docker API to Docker PY.
    :param daemon_client: optional configuration for client creation
    """

    daemon_client = daemon_client or {}
    client = docker_client.get_client(daemon_client)

    arguments = dict()
    arguments['repository'] = ctx.node.properties['repository']
    arguments['src'] = ctx.node.properties['src']
    arguments.update(ctx.node.properties['params'].copy())

    ctx.logger.info('Importing image.')
    ctx.logger.debug('Provded params: {}'.format(arguments))

    try:
        output = client.import_image(**arguments)
    except docker.errors.APIError as e:
        raise NonRecoverableError('Unable to import image: '
                                  '{0}.'.format(str(e)))

    ctx.logger.info('output: {}'.format(output))

    image_id = utils.get_newest_image_id(client)
    ctx.instance.runtime_properties['image_id'] = image_id
    ctx.logger.info('Image import successful. Image: {0}'.format(image_id))


@operation
def create_container(daemon_client=None, **_):
    """ cloudify.docker.container type create lifecycle operation.
        Creates a container that can then be .start() ed.

    :node_property use_external_resource: True or False. Use existing
        instead of creating a new resource.
    :node_property resource_id:  The container name.
    :node_property image: The image to run.
    :node_property ports: A dictionary with pairs of port bindings
        as provided to the start function. The create function
        will pass only the dict keys as the ports parameter and
        the start function will pass the pairs as port bindings.
    :param daemon_client: optional configuration for client creation
    """

    daemon_client = daemon_client or {}
    client = docker_client.get_client(daemon_client)

    if ctx.node.properties['use_external_resource']:
        if 'name' not in ctx.node.properties:
            raise NonRecoverableError('Use external resource, but '
                                      'no resource id provided.')
        ctx.instance.runtime_properties['container_id'] = \
            utils.get_container_id_from_name(ctx.node.properties['name'],
                                             client, ctx=ctx)
        return

    arguments = dict()
    arguments = utils.get_create_container_params(ctx=ctx)
    arguments['name'] = ctx.node.properties['name']
    arguments['image'] = ctx.node.properties['image']

    if ctx.node.properties.get('ports'):
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
    """ cloudify.docker.container type start lifecycle operation.
        Any properties and runtime_properties set in the create
        lifecycle operation also available in start.
        Similar to the docker start command, but doesn't support
        attach options.

    :param daemon_client: optional configuration for client creation
    :param retry_interval: The number of seconds between retries during
        the wait_for_processes bit.
    """

    daemon_client = daemon_client or {}
    client = docker_client.get_client(daemon_client)

    if ctx.node.properties['use_external_resource']:
        if utils.get_container_info(client, ctx=ctx) is None:
            raise NonRecoverableError('{} does not exist.'.format(
                ctx.instance.runtime_properties.get('container_id')))

    arguments = dict()
    arguments = utils.get_start_params(ctx=ctx)
    arguments['container'] = \
        ctx.instance.runtime_properties['container_id']

    ctx.logger.info('Starting container.')

    try:
        response = client.start(**arguments)
    except docker.errors.APIError as e:
        raise NonRecoverableError('Failed to start container: '
                                  '{0}.'.format(str(e)))

    ctx.logger.info('Container started: {}.'.format(response))

    if ctx.node.properties[('params')].get('processes_to_wait_for', False):
        utils.wait_for_processes(retry_interval, client, ctx=ctx)

    ctx.logger.info('Started container: {0}.'.format(
        ctx.instance.runtime_properties['container_id']))

    if utils.get_container_info(client, ctx=ctx) is not None:
        inspect_output = utils.inspect_container(client)
        ctx.instance.runtime_properties['ports'] = \
            inspect_output.get('Ports', None)
        ctx.instance.runtime_properties['network_settings'] = \
            inspect_output.get('NetworkSettings', None)
        ctx.instance.runtime_properties['ip'] = \
            inspect_output['NetworkSettings'].get('IPAddress')

    top_info = utils.get_top_info(client)

    ctx.logger.info('Container: {0} Forwarded ports: {1} Top: {2}.'.format(
        ctx.instance.runtime_properties['container_id'],
        inspect_output.get('Ports', None), top_info))


@operation
def stop(retry_interval, timeout, daemon_client=None, **_):
    """ cloudify.docker.container type stop lifecycle operation.
        Stops a container. Similar to the docker stop command.
        Any properties and runtime_properties set in the create
        and start lifecycle operations also available in stop.

    :param daemon_client: optional configuration for client creation
    :param timeout: Timeout in seconds to wait for the container to stop before
        sending a SIGKILL.
    """

    daemon_client = daemon_client or {}
    client = docker_client.get_client(daemon_client)

    container = ctx.instance.runtime_properties['container_id']
    ctx.logger.info('Stopping container: {}'.format(container))

    try:
        client.stop(container, timeout)
    except docker.errors.APIError as e:
        raise NonRecoverableError('Failed to stop container: '
                                  '{0}'.format(str(e)))

    if 'Exited' not in utils.check_container_status(client, ctx=ctx):
        raise RecoverableError('Container still running. Retyring.',
                               retry_after=retry_interval)

    ctx.logger.info('Stopped container: {}'.format(container))


@operation
def remove_container(v, link, force, daemon_client=None, **_):
    """ cloudify.docker.container type delete lifecycle operation.
        Any properties and runtime_properties set in the create,
        start, and stop lifecycle operations also available in
        delete.
        Remove a container. Similar to the docker rm command.

    :param v: Remove the volumes associated with the container.
    :param link: Remove the specified link and not the underlying container.
    :param force: force the removal of a running container (uses SIGKILL)
    :param daemon_client: optional configuration for client creation
    """
    daemon_client = daemon_client or {}
    client = docker_client.get_client(daemon_client)

    container = ctx.instance.runtime_properties['container_id']
    ctx.logger.info('Removing container {}'.format(container))

    try:
        client.remove_container(container, v, link, force)
    except docker.errors.APIError as e:
        raise NonRecoverableError('Failed to delete container: '
                                  '{0}.'.format(str(e)))
    finally:
        del(ctx.instance.runtime_properties['container_id'])

    ctx.logger.info('Removed container {}'.format(container))


@operation
def remove_image(force, noprune, daemon_client=None, **_):
    """ cloudify.docker.Image type delete lifecycle operation.
        Any properties and runtime_properties set in the create
        lifecycle operation are also available in delete.
        Removes an image. Similar to the docker rmi command.

    :param force: Force removal of the image
    :param noprune: Do not delete untagged parents
    """

    daemon_client = daemon_client or {}
    client = docker_client.get_client(daemon_client)

    image = ctx.instance.runtime_properties['image_id']
    ctx.logger.info('Removing image: {}'.format(image))

    try:
        client.remove_image(image, force, noprune)
    except docker.errors.APIError as e:
        raise NonRecoverableError('Failed to delete image: '
                                  '{}.'.format(str(e)))
    finally:
        del(ctx.instance.runtime_properties['image_id'])

    ctx.logger.info('Removed image: {}'.format(image))
