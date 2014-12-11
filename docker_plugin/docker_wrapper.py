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

"""Functions that wrap docker functions."""


import re

import time
import docker

from cloudify import ctx
from cloudify import exceptions


_ERR_MSG_UNKNOWN_IMAGE_IMPORT = 'Unknown error during image import'
_ERR_MSG_UNKNOWN_IMAGE_BUILD = 'Unknown error while building image'

# Postision of image id in image_import result
_IMAGE_IMPORT_ID_POSITION = 2
# Postision of error in image_import result
_IMAGE_IMPORT_ERROR_POSITION = 2
# Postision of image id in image_build result
_IMAGE_BUILD_ID_POSITION = 3


def _is_image_id_valid(image_id):
    return re.match('^[a-f0-9]{12,64}$', image_id) is not None


def _get_import_image_id(client, import_image_output):
    # It is useful beacause
    # import_image returns long string where in the second line
    # after last status is image id
    unknow_error_message = '{0} (import image output: {1})'.format(
        _ERR_MSG_UNKNOWN_IMAGE_IMPORT, import_image_output)
    try:
        output_line = import_image_output.split('\n')[-2]
    except IndexError:
        _log_and_raise(client, unknow_error_message)
    position_of_last_status = output_line.rfind('status')
    if position_of_last_status < 0:
        # If there was an error, there is no 'status'
        # in second output line
        # error message is after last 'error'
        position_of_error = output_line.rfind('error')
        try:
            err_msg = output_line[position_of_error:].\
                split('"')[_IMAGE_IMPORT_ERROR_POSITION]
        except IndexError:
            _log_and_raise(client, unknow_error_message)
        err_msg = 'Error during image import {}'.format(err_msg)
        _log_and_raise(client, err_msg)
    try:
        image_id = output_line[position_of_last_status:].\
            split('"')[_IMAGE_IMPORT_ID_POSITION]
    except IndexError:
        _log_and_raise(client, unknow_error_message)
    else:
        if _is_image_id_valid(image_id):
            return image_id
        else:
            _log_and_raise(client, unknow_error_message)


def _get_build_image_id(client, stream_generator):
    stream = None
    for stream in stream_generator:
        pass
    # Fourth word in a string stream is an id
    if stream is None:
        _log_and_raise(
            client,
            _ERR_MSG_UNKNOWN_IMAGE_BUILD,
            exceptions.RecoverableError
        )
    try:
        image_id = re.sub(r'[\W_]+', ' ', stream).\
            split()[_IMAGE_BUILD_ID_POSITION]
    except IndexError:
        _log_and_raise(client, _ERR_MSG_UNKNOWN_IMAGE_BUILD)
    if _is_image_id_valid(image_id):
        return image_id
    else:
        _log_and_raise(
            client,
            _ERR_MSG_UNKNOWN_IMAGE_BUILD
        )


def _get_container_or_raise(client):
    container = ctx.instance.runtime_properties.get('container')
    if container is None:
        _log_and_raise(client, 'No container specified')
    return container


def _get_image_or_raise(client, container_config=None):
    image = container_config.pop('image', None)
    if image:
        ctx.instance.runtime_properties['using_local_image'] = True
    else:
        image = ctx.instance.runtime_properties.get('image')
        ctx.instance.runtime_properties['using_local_image'] = False
    if not image:
        _log_and_raise(client, 'No image specified')
    return image


def _log_container_info(message=''):
    if 'container' in ctx.instance.runtime_properties:
        message = '{} {}'.format(message,
                                 ctx.instance.runtime_properties['container'])
    ctx.logger.info(message)


def _log_and_raise(client,
                   err_msg='',
                   exc_class=exceptions.NonRecoverableError):
    _log_error_container_logs(client, err_msg)
    raise exc_class(err_msg)


def _log_error_container_logs(client, message=''):
    container = ctx.instance.runtime_properties.get('container')
    if container is not None:
        if message:
            message += '\n'
        message += 'Container: {}'.format(container)
        try:
            logs = client.logs(container)
        except docker.errors.APIError as e:
            ctx.logger.error(str(e))
        else:
            if logs:
                message += '\nLogs:\n{}'.format(logs)
    if message:
        ctx.logger.error(message)


def get_top_info(client):
    """Get container top info.

    Get container top info using docker top function with container id
    from ctx.instance.runtime_properties['container'].

    Transforms data into a simple top table.

    :param client: docker client
    :return: top_table
    :rtype: str
    :raises NonRecoverableError:
        when container in ctx.instance.runtime_properties is None.

    """

    def format_as_table(top_dict):
        top_table = ' '.join(top_dict['Titles']) + '\n'
        top_table += '\n'.join(' '.join(p) for p in top_dict['Processes'])
        return top_table

    _log_container_info('getting TOP info of container')
    container = _get_container_or_raise(client)
    try:
        top_dict = client.top(container)
    except docker.errors.APIError as e:
        _log_and_raise(client, str(e))
    else:
        return format_as_table(top_dict)


def get_container_info(client):
    """Get container info.

    Get list of containers dictionaries from docker containers function.
    Find container which is specified in
    ctx.instance.runtime_properties['container'].

    :param client: docker client
    :return: container_info
    :rtype: dict

    """

    container = ctx.instance.runtime_properties.get('container')
    if container is not None:
        for c in client.containers():
            if container in c.itervalues():
                return c
    return None


def inspect_container(client):
    """Inspect container.

    Call inspect with container id from
    ctx.instance.runtime_properties['container'].

    :param client: docker client
    :return: container_info
    :rtype: dict

    """

    container = ctx.instance.runtime_properties.get('container')
    if container is not None:
        return client.inspect_container(container)
    return None


def set_env_var(client, container_config):
    """Set environmental variables.

    Set variables from ctx.instance.runtime_properties['docker_env_var']
    to enviromental variables, which will be added to variables from
    container_create['enviroment'] and relayed to container.

    :param client: docker client
    :param container_config: configuration to create container

    """
    environment = container_config.get('environment', {})
    for key, value in ctx.instance.runtime_properties.get(
            'docker_env_var', {}).items():
        if key not in environment:
            environment[str(key)] = str(value)
    container_config['environment'] = environment


def get_client(daemon_client):
    """Get client.

    Returns docker client using daemon_client as configuration.

    :param daemon_client: optional configuration for client creation
    :raises NonRecoverableError:
        when docker.errors.APIError during client.
    :return: docker client
    :rtype: docker.Client

    """
    try:
        return docker.Client(**daemon_client)
    except docker.errors.DockerException as e:
        error_msg = 'Error while getting client: {}'.format(str(e))
        _log_and_raise(daemon_client, error_msg)


def pull_image(client, image_pull):
    """Pull an image

    Pull an image from the docker hub
    :param client: docker client
    :param image_pull: confoguration for pulling the image
    :raises NonRecoverableError:
        when failing to pull the image

    """
    ctx.logger.info('Pulling image')

    image_pull_repo = image_pull.get('repository')
    if not image_pull_repo:
        _log_and_raise(client=client, err_msg='Missing repository name')
    stream = image_pull.get('stream')
    if stream is False:
        ctx.logger.warn("Streaming will be set to True although False \
            was specified")
    image_pull['stream'] = True

    for line in client.pull(**image_pull):
        ctx.logger.info(line)


def import_image(client, image_import):
    """Import image.

    Import image from 'image_import'.
    'src' in 'image_import' must be specified.

    :param client: docker client
    :param image_import: configuration for importing image
    :raises NonRecoverableError:
        when no 'src' in 'image_import' or when there was
        a problem during image download.
    :return: image_id, valid docker image id
    :rtype: str

    """

    ctx.logger.info('Importing image')
    import_image_output = client.import_image(**image_import)
    image_id = _get_import_image_id(
        client, import_image_output)
    ctx.logger.info('Image {} has been imported'.format(image_id))
    return image_id


def build_image(client, image_build):
    """Build image.

    Build image from 'image_build'.
    'path' in 'image_build' must be specified.

    :param client: docker client
    :param image_build: configuration for building image
    :return: image_id, valid docker image id
    :rtype: str
    :raises NonRecoverableError:
        when no 'path' in 'image_build'
        or when there was a problem during image download.

    """

    ctx.logger.info(
        'Building image from path {}'.format(
            image_build['path']))
    try:
        image_stream = client.build(**image_build)
    except OSError as e:
        error_msg = 'Error while building image: {}'.format(str(e))
        _log_and_raise(client, error_msg)
    else:
        image_id = _get_build_image_id(client, image_stream)
        ctx.logger.info('Image {} has been built'.format(image_id))
        return image_id


def create_container(client, container_config):
    """Create container.

    Create container from image which id is specified in
    ctx.instance.runtime_properties
    ['container'] with options from 'container_config'.
    In those options at least 'command' must be specified.

    Set container id in ctx.instance.runtime_properties['container'].

    :param client: docker client
    :param container_config: configuration for creating container
    :raises NonRecoverableError:
        when 'image' in ctx.instance.runtime_properties is None
        or when docker.errors.APIError (for example when 'command' is
        not specified in 'container_config'.

    """

    ctx.logger.info('Creating container')
    image = _get_image_or_raise(client, container_config)
    try:
        cont = client.create_container(image, **container_config)
    except docker.errors.APIError as e:
        error_msg = 'Error while creating container: {}'.format(str(e))
        _log_and_raise(client, error_msg)
    else:
        ctx.instance.runtime_properties['container'] = cont['Id']
    _log_container_info('Created container')


def start_container(client, processes_to_wait_for, container_start):
    """Start container.

    Start container which id is specified in ctx.instance.runtime_properties
    ['container'] with optional options from 'container_start'.

    :param client: docker client
    :param processes_to_wait_for: dict for specifying processes for which
                                  this call should block until they all
                                  exist
    :param container_start: configuration for starting a container
    :raises NonRecoverableError:
        when 'container' in ctx.instance.runtime_properties is None
        or when docker.errors.APIError.

    """

    _log_container_info('Starting container')
    container = _get_container_or_raise(client)
    try:
        client.start(container, **container_start)
        processes_to_wait_for = processes_to_wait_for or {}
        if processes_to_wait_for.get('process_names'):
            process_names = processes_to_wait_for.get('process_names')
            wait_for_time = processes_to_wait_for.get('wait_for_time_secs', 0)
            interval = processes_to_wait_for.get('interval', 5)
            all_active = _wait_for_processes(client,
                                             container,
                                             process_names,
                                             wait_for_time,
                                             interval)
            if not all_active:
                _log_and_raise(client, 'one of the following processes was not \
                               started in the container: {}'
                               .format(process_names))
    except docker.errors.APIError as e:
        _log_and_raise(client, str(e))
    _log_container_info('Started container')


def _wait_for_processes(client, container, process_names, timeout, interval):
    ctx.logger.info('waiting for the following processeses: {}'
                    .format(process_names))
    if timeout:
        ctx.logger.info('about to wait for {} seconds for processes to start'
                        .format(timeout))

    end = time.time() + timeout
    while True:
        top_result = client.top(container)
        top_result_processes = top_result.get('Processes')
        all_active = all([
            any([
                # last element of list is the command executed
                process_name in top_result_process[-1]
                for top_result_process in top_result_processes
            ])
            for process_name in process_names
        ])
        if all_active or time.time() >= end:
            ctx.logger.info('Container.top(): {}'.format(top_result))
            return all_active
        time.sleep(interval)


def stop_container(client, container_stop):
    """Stop container.

    Stop container which id is specified in ctx.instance.runtime_properties
    ['container'] with optional options from 'container_stop'.

    :param client: docker client
    :param container_stop: configuration for stopping a container
    :raises NonRecoverableError:
        when 'container' in ctx.instance.runtime_properties is None
        or when docker.errors.APIError.

    """

    _log_container_info('Stopping container')
    container = _get_container_or_raise(client)
    try:
        client.stop(container, **container_stop)
    except docker.errors.APIError as e:
        _log_and_raise(client, str(e))
    _log_container_info('Stopped container')


def remove_container(client, container_remove):
    """Remove container.

    Remove container which id is specified in ctx.instance.runtime_properties
    ['container'] with optional options from 'container_remove'.

    :param client: docker client
    :param container_remove: coniguration for removing container
    :raises NonRecoverableError:
        when 'container' in ctx.instance.runtime_properties is None
        or 'remove_image' in 'container_remove' is True
        and 'image' in ctx.instance.runtime_properties is None
        or when docker.errors.APIError.

    """

    container = _get_container_or_raise(client)
    ctx.logger.info('Removing container {}'.format(container))
    try:
        client.remove_container(container, **container_remove)
    except docker.errors.APIError as e:
        _log_and_raise(client, str(e))
    ctx.logger.info('Removed container {}'.format(container))


def remove_image(client):
    """Remove image.

    Remove image whose id is specified in
    ctx.instance.runtime_properties['image'].
    If the user used a locally built image do nothing

    :param client: docker client
    :raises NonRecoverableError:
        when 'image' in ctx.instance.runtime_properties is None
        or when docker.errors.APIError while removing image (for example
        if image is used by another container).

    """
    if ctx.instance.runtime_properties.get('using_local_image') is True:
        ctx.logger.debug('remove_image called, doing nothing since user used \
         a local image')
        return

    image = _get_image_or_raise(client)
    _log_container_info('Removing image {}, container:'.format(image))
    try:
        client.remove_image(image)
    except docker.errors.APIError as e:
        _log_and_raise(client, str(e))
    _log_container_info('Removed image {}, container:'.format(image))
