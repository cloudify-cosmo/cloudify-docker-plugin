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
from docker.errors import APIError

# Cloudify Imports
from cloudify import ctx
from cloudify.exceptions import RecoverableError, NonRecoverableError


def get_image_id(tag, repository, client):

    try:
        images = client.images()
    except APIError as e:
        raise NonRecoverableError(
            'Unable to get last created image: {0}'.format(e))

    for image in images:
        if '{0}:{1}'.format(repository, tag) in image.get('RepoTags'):
            return image.get('Id')

    raise NonRecoverableError(
        'Could not find an image that matches repository:tag'
        ' {0}:{1}.'.format(repository, tag))


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
        except APIError as e:
            raise NonRecoverableError(
                'Unable to inspect container: {0}'.format(str(e)))
        else:
            return output
    else:
        return None


def wait_for_processes(process_names, retry_interval, client):
    """ The user may provide a node param in the blueprint wait_for_processes.
        This is a list of processes to verify are active on the container
        before completing the start operation. If all processes are not active
        the function will be retried.

    :param retry_interval: the number of seconds between retries.
    :param client: the client. see docker_client.
    :param ctx: the cloudify context.
    """

    ctx.logger.info('Waiting for these processes to finish: '
                    '{0}'.format(process_names))

    container = ctx.instance.runtime_properties.get('container_id')

    try:
        top_result = client.top(container)
    except APIError as e:
        raise NonRecoverableError(
            'Unable get container processes from top: {0}'.format(str(e)))

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
        ctx.logger.info('Container.top(): {0}'.format(top_result))
        return all_active
    else:
        raise RecoverableError(
            'Waiting for all these processes. Retrying...',
            retry_after=retry_interval)


def get_container_dictionary(client):
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

    container_id = ctx.instance.runtime_properties.get('container_id')
    if container_id is None:
        ctx.logger.debug(
            'Unable to retrieve container dictionary.'
            'ctx container ID value is None')
        return None

    try:
        all_containers = client.containers(all=True)
    except APIError as e:
        raise NonRecoverableError(
            'Unable to list all containers: {0}.'.format(str(e)))

    for container in all_containers:
        if container_id in container.get('Id'):
            return container
        else:
            ctx.logger.debug(
                'Unable to retrieve container dictionary.'
                'container with ID {0} does not exist.'
                .format(container_id))
            return None


def check_container_status(client):
    """ Gets the status value from the container info dictionary

    :param client: the client. see docker_client.
    :param ctx: the cloudify context.
    returns status or None if not found.
    """

    container = get_container_dictionary(client)
    if container is None:
        return None
    return container.get('Status', None)


def get_container_id_from_name(name, client):
    """ Queries the local list of containers for a container with name.

    :param name: the name of a container.
    :param client: the client. see docker_client.
    :param ctx: the cloudify context.
    if name is in the list of containers return the id of the container.
    if name is not in the list of containers raise NonRecoverableError
    """

    for n, i in [(c.get('Names'), c.get('Id'))
                 for c in client.containers(all=True)]:
        if name in n:
            return i
        else:
            raise NonRecoverableError(
                'No such container: {0}.'.format(name))


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
    except APIError as e:
        raise NonRecoverableError(
            'Unable get container processes from top: {0}'.format(str(e)))
    else:
        return format_as_table(top_dict)
