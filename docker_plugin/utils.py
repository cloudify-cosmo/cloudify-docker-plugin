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
import docker

# Cloudify Imports
from cloudify import ctx
from cloudify.exceptions import RecoverableError, NonRecoverableError


def get_image_id(tag, image_id, client):
    """ Attempts to get the correct image id from Docker.

    :param tag: The image tag provided in the blueprint.
    :param image_id: The last id extracted from the stream
        during the image pull process.
    :param client: docker client
    returns image id
        if the last extracted image id matches the tag
        and the image id for that tag matches the pulled
        image id then that image id is used
        if the image id only matches an image id in docker
        then that is used
        if no match is found the image id initially passed is
        kept
    """

    ctx.logger.debug('This image id {} is an image id stub and '
                     'was the last image id captured during '
                     'the pull operation. If you provided a '
                     'tag, it might not match the image id of '
                     'the tagged image. So this operation '
                     'searches for an id that matches that tag. '
                     'If there is no tag match and only a match '
                     'between image ids then the complete id is '
                     'returned. If there is no match at all, the '
                     'image_id stub is returned.'.format(image_id))

    try:
        images = client.images()
    except docker.errors.APIError as e:
        raise NonRecoverableError('Unable to get last created image: '
                                  '{}'.format(e))

    for img in images:
        img_id, tags = (str(img.get('Id')), img.get('RepoTags'))
        if filter(None, [repotag if
                  tag in repotag else None for repotag in tags]) \
                and str(image_id) in img_id:
            ctx.logger.debug(
                'The tags and ids match, '
                'assigning this image id: {}.'.format(img_id))
            return img_id
        elif str(image_id) in img_id:
            ctx.logger.debug(
                'No tags match, assigning this image id: {}.'.format(img_id))
            return img_id

    ctx.logger.debug('Unable to verify that the image id '
                     'received during pull is valid.')

    ctx.logger.info('Returning image id {}.'.format(image_id))
    return str(image_id)


def inspect_container(client):
    """Inspect container.

    Call inspect with container id from
    ctx.instance.runtime_properties['container_id'].

    :param client: docker client
    :return: container_info
    """

    container = ctx.instance.runtime_properties.get('container_id')

    if container is not None:
        try:
            output = client.inspect_container(container)
        except docker.errors.APIError as e:
            raise NonRecoverableError('Unable to inspect container: '
                                      '{}'.format(str(e)))
        else:
            return output
    else:
        return None


def get_top_info(client):
    """Get container top info.
    Get container top info using docker top function with container id
    from ctx.instance.runtime_properties['container'].
    Transforms data into a simple top table.

    :param client: docker client
    :return: top_table
    :raises NonRecoverableError:
        when container in ctx.instance.runtime_properties is None.
    """

    def format_as_table(top_dict):
        top_table = ' '.join(top_dict['Titles']) + '\n'
        top_table += '\n'.join(' '.join(p) for p in top_dict['Processes'])
        return top_table

    ctx.logger.info('Getting TOP info of container.')

    container = ctx.instance.runtime_properties.get('container_id')

    try:
        top_dict = client.top(container)
    except docker.errors.APIError as e:
        raise NonRecoverableError('Unable get container processes from top: '
                                  '{}'.format(str(e)))
    else:
        return format_as_table(top_dict)


def wait_for_processes(retry_interval, client, ctx):
    """ The user may provide a node param in the blueprint wait_for_processes.
        This is a list of processes to verify are active on the container
        before completing the start operation. If all processes are not active
        the function will be retried.

    :param retry_interval: the number of seconds between retries.
    :param client: the client. see docker_client.
    :param ctx: the cloudify context.
    """
    process_names = ctx.node.properties.get('params').get(
        'processes_to_wait_for', False)

    ctx.logger.info('Waiting for these processes to finish: '
                    '{}'.format(process_names))

    container = ctx.instance.runtime_properties.get('container_id')

    try:
        top_result = client.top(container)
    except docker.errors.APIError as e:
        raise NonRecoverableError('Unable get container processes from top: '
                                  '{}'.format(str(e)))

    top_result_processes = top_result.get('Processes')
    all_active = all([
        any([
            # last element of list is the command executed
            process_name in top_result_process[-1]
            for top_result_process in top_result_processes
        ])
        for process_name in process_names
    ])
    if all_active:
        ctx.logger.info('Container.top(): {}'.format(top_result))
        return all_active
    else:
        raise RecoverableError('Waiting for all these processes. Retrying...',
                               retry_after=retry_interval)


def get_container_info(client, ctx):
    """ Gets the container ID from the cloudify context.
        Searches Docker for that container ID.
        Returns dockers dictionary for that container ID.



    Get list of containers dictionaries from docker containers function.
    Find container which is specified in
    ctx.instance.runtime_properties['container'].

    :param client: the client. see docker_client.
    :param ctx: the cloudify context.
    :return: container dictionary
    """

    if ctx.instance.runtime_properties.get('container_id') is None:
        return None

    try:
        all_containers = client.containers(all=True)
    except docker.errors.APIError as e:
        raise NonRecoverableError('Unable to list all containers: '
                                  '{}.'.format(str(e)))

    for container in all_containers:
        if ctx.instance.runtime_properties.get('container_id') in \
                container.get('Id'):
            return container
        else:
            return None


def get_start_params(ctx):
    """ Maintain the list of supported parameters for the docker API
        start function. use this with get_params.

    :param ctx: the cloudify context.
    returns the dictionary returned from get_params.
    """

    supported_params = \
        ['binds', 'lxc_conf', 'publish_all_ports', 'links',
            'privileged', 'dns', 'dns_search', 'volumes_from',
            'network_mode', 'restart_policy', 'cap_add',
            'cap_drop', 'extra_hosts']

    return get_params(supported_params)


def get_create_container_params(ctx):
    """ Maintain the list of supported parameters for the docker API
        create function. use this with get_params.

    :param ctx: the cloudify context.
    returns the dictionary returned from get_params.
    """

    supported_params = \
        ['command', 'hostname', 'user', 'detach', 'stdin_open',
            'tty', 'mem_limit', 'environment', 'dns',
            'volumes', 'volumes_from', 'network_disabled',
            'entrypoint', 'cpu_shares', 'working_dir',
            'domainname', 'memswap_limit', 'host_config']

    return get_params(supported_params)


def get_params(supported_params):
    """ Give this method a list of supported parameters and it
        retrieves the node property value provided by the user
        in the blueprint. This can be used as kwargs in an API
        call.

    :param supported_params: a list of supported parameters
    returns a dictionary of parameters
    """

    d = {}

    for key in ctx.node.properties['params'].keys():
        if key in supported_params:
            d[key] = ctx.node.properties['params'].get(key)

    return d


def check_container_status(client, ctx):
    """ Gets the status value from the container info dictionary

    :param client: the client. see docker_client.
    :param ctx: the cloudify context.
    returns status
    """

    container = get_container_info(client, ctx=ctx)
    status = container.get('Status')
    return status


def get_container_id_from_name(name, client, ctx):
    """ Queries the local list of containers for a container with name.

    :param name: the name of a container.
    :param client: the client. see docker_client.
    :param ctx: the cloudify context.
    if name is in the list of containers return the id of the container.
    if name is not in the list of containers raise NonRecoverableError
    """

    for n, i in \
            [(c.get('Names'),
              c.get('Id')) for c in client.containers(all=True)]:
        if name in n:
            return i
        else:
            raise NonRecoverableError('No such container: {}.'.format(name))
