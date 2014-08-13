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


import netifaces

from cloudify import exceptions
from cloudify.decorators import operation

import docker_plugin.docker_wrapper as docker_wrapper


_ERR_MSG_NO_IMAGE_SRC = 'Either path or url to image must be given'
_ERR_MSG_TWO_IMAGE_SRC = ('Image import url and image build path specified'
                          ' There can only be one image source')
_LOOPBACK_INTERFACE = 'lo'
_ADDRESS = 'addr'


def _get_host_ips():
    host_ips = {}
    for i in netifaces.interfaces():
        ifaddresses = netifaces.ifaddresses(i)
        if (
            i != _LOOPBACK_INTERFACE and
            netifaces.AF_INET in ifaddresses
        ):
            host_ips.update({i: ifaddresses[netifaces.AF_INET][0][_ADDRESS]})
    return host_ips


@operation
def create(ctx, *args, **kwargs):
    """Create image.

    RPC called by Cloudify Manager.

    If 'src' is specified in 'import_image' then
    Import image using ctx.properties['image_build'] as options.
    Otherwise If 'path' is specified in 'build_image' then
    Build image using ctx.properties['image_build'] as options.
    Otherwise error is raised.

    Set imported image_id in ctx.runtime_properties['image'].

    Set variables from ctx.properties that are not used by cloudify plugin
    to enviromental variables, which will be added to variables from
    ctx.properties['container_create']['enviroment'] and relayed to container.

    Create container from imported image with options from
    ctx.properties['container_create'].
    'command' in ctx.properties['container_create'] must be specified.

    Args:
        ctx (cloudify context)

    Raises:
        NonRecoverableError: when 'src' in ctx.properties['image_import']
            and 'path' in ctx.properties are both not specified
            or are both specified.

    """

    client = docker_wrapper.get_client(ctx)
    image_import = ctx.properties.get('image_import', {}).get('src')
    image_build = ctx.properties.get('image_build', {}).get('path')
    if image_import and image_build:
        ctx.logger.error(_ERR_MSG_TWO_IMAGE_SRC)
        raise exceptions.NonRecoverableError(_ERR_MSG_TWO_IMAGE_SRC)
    elif image_import:
        image = docker_wrapper.import_image(ctx, client)
    elif image_build:
        image = docker_wrapper.build_image(ctx, client)
    else:
        ctx.logger.error(_ERR_MSG_NO_IMAGE_SRC)
        raise exceptions.NonRecoverableError(_ERR_MSG_NO_IMAGE_SRC)
    ctx.runtime_properties['image'] = image


@operation
def configure(ctx, *args, **kwargs):
    """Create container using image from ctx.runtime_properties.

    RPC called by Cloudify Manager.

    Add variables from ctx.runtime_properties['docker_env_var'] to variables
    from ctx.properties['container_create']['enviroment'] and
    relayed to container as enviromental variables.

    Create container from image from ctx.runtime_properties with options from
    ctx.properties['container_create'].
    'command' in ctx.properties['container_create'] must be specified.

    Args:
        ctx (cloudify context)

    Raises:
        NonRecoverableError: when docker.errors.APIError during start
            (for example when 'command' is not specified in
            ctx.properties['container_create']).

    """

    client = docker_wrapper.get_client(ctx)
    docker_wrapper.set_env_var(ctx, client)
    docker_wrapper.create_container(ctx, client)


@operation
def run(ctx, *args, **kwargs):
    """Run container.

    RPC called by Cloudify Manager.

    Run container which id is specified in ctx.runtime_properties['container']
    with optional options from ctx.properties['container_start'].

    Retreives host IP, forwarded ports and top info about the container
    from the Docker and log it. Additionally sets in ctx.runtime_properties:
    -   host_ip (dictionary of strings)
    -   forwarded ports (list)
    -   Docker's networkSettings (dictionary)

    Args:
        ctx (cloudify context)

    Raises:
        NonRecoverableError: when 'container' in ctx.runtime_properties is None
            or when docker.errors.APIError during start.

    Logs:
       Container id,
       List of network interfaces with IPs,
       Container ports,
       Container top information

    """

    client = docker_wrapper.get_client(ctx)
    docker_wrapper.start_container(ctx, client)
    container = docker_wrapper.get_container_info(ctx, client)
    container_inspect = docker_wrapper.inspect_container(ctx, client)
    ctx.runtime_properties['host_ips'] = _get_host_ips()
    ctx.runtime_properties['ports'] = container['Ports']
    ctx.runtime_properties['networkSettings'] = \
        container_inspect['NetworkSettings']
    log_msg = (
        'Container: {}\nHost IPs: {}\nForwarded ports: {}\nTop: {}'
    ).format(
        container['Id'],
        ctx.runtime_properties['host_ips'],
        str(ctx.runtime_properties['ports']),
        docker_wrapper.get_top_info(ctx, client)
    )
    ctx.logger.info(log_msg)


@operation
def stop(ctx, *args, **kwargs):
    """Stop container.

    RPC called by Cloudify Manager.

    Stop container which id is specified in ctx.runtime_properties
    ['container'] with optional options from ctx.properties['container_stop'].

    Args:
        ctx (cloudify context)

    Raises:
        NonRecoverableError: when 'container' in ctx.runtime_properties is None
            or when docker.errors.APIError during stop.

    """

    client = docker_wrapper.get_client(ctx)
    docker_wrapper.stop_container(ctx, client)


@operation
def delete(ctx, *args, **kwargs):
    """Delete container.

    RPC called by Cloudify Manager.

    Remove container which id is specified in ctx.runtime_properties
    ['container'] with optional options from
    ctx.properties['container_remove'].

    If container is running stop it.
    if ctx['container_remove']['remove_image'] is True then remove image.

    Args:
        ctx (cloudify context)

    Raises:
        NonRecoverableError: when 'container' in ctx.runtime_properties is None
            or 'remove_image' in ctx.properties['container_remove'] is True
            and 'image' in ctx.runtime_properties is None
            or when docker.errors.APIError during stop, remove_container,
            remove_image (for example if image is used by another container).

    """

    client = docker_wrapper.get_client(ctx)
    container_info = docker_wrapper.inspect_container(ctx, client)
    if container_info and container_info['State']['Running']:
        docker_wrapper.stop_container(ctx, client)
    remove_image = ctx.properties.get('container_remove', {}).pop(
        'remove_image', None
    )
    docker_wrapper.remove_container(ctx, client)
    if remove_image:
        docker_wrapper.remove_image(ctx, client)
