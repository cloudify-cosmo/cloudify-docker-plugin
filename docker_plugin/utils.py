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
from retrying import retry
import docker

# Cloudify Imports
from cloudify import ctx
from cloudify.exceptions import RecoverableError, NonRecoverableError


def build_arg_dict(user_supplied, unsupported):

    arguments = {}
    for pair in user_supplied.items():
        arguments['{0}'.format(pair[0])] = pair[1]
    for pair in unsupported.items():
        arguments['{0}'.format(pair[0])] = pair[1]
    return arguments


def get_container_info(client):
    """Get container info.

    Get list of containers dictionaries from docker containers function.
    Find container which is specified in
    ctx.instance.runtime_properties['container'].

    :param client: docker client
    :return: container_info
    :rtype: dict

    """

    if ctx.instance.runtime_properties.get('container_id') is not None:
        all_containers = client.containers(all=True)
        for container in all_containers:
            if ctx.instance.runtime_properties.get('container_id') in \
                    container.get('Id'):
                return container
            else:
                return None


def inspect_container(client):
    """Inspect container.

    Call inspect with container id from
    ctx.instance.runtime_properties['container'].

    :param client: docker client
    :return: container_info
    :rtype: dict

    """

    container = ctx.instance.runtime_properties.get('container_id')

    if container is not None:
        return client.inspect_container(container)
    return None


def validate_container_ready(ctx):
    """ Checks the containers processes
        and makes sure the container is ready to be used
    """
    ctx.instance.runtime_properties['container_id']


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

    ctx.logger.info('Getting TOP info of container.')

    container = ctx.instance.runtime_properties.get('container_id')

    try:
        top_dict = client.top(container)
    except docker.errors.APIError as e:
        raise NonRecoverableError('Unable get container processes from top: '
                                  '{}'.format(str(e)))
    else:
        return format_as_table(top_dict)


@retry
def wait_for_processes(retry_interval, client, ctx):

    process_names = ctx.node.properties.get('params').get(
        'processes_to_wait_for', False)

    ctx.logger.info('Waiting for these processes to finish: '
                    '{}'.format(process_names))

    container = ctx.instance.runtime_properties.get('container_id')

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
    if all_active:
        ctx.logger.info('Container.top(): {}'.format(top_result))
        return all_active
    else:
        raise RecoverableError('Waiting for all these processes. Retrying...',
                               retry_after=retry_interval)


def get_start_params(ctx):

    d = {}

    supported_params = \
        ['binds', 'lxc_conf', 'publish_all_ports', 'links',
            'privileged', 'dns', 'dns_search', 'volumes_from',
            'network_mode', 'restart_policy', 'cap_add',
            'cap_drop', 'extra_hosts']

    for key in ctx.node.properties['params'].keys():
        if key in supported_params:
            d[key] = ctx.node.properties['params'].get(key)

    return d


def get_create_container_params(ctx=ctx):

    d = {}

    supported_params = \
        ['command', 'hostname', 'user', 'detach', 'stdin_open',
            'tty', 'mem_limit', 'ports', 'environment', 'dns',
            'volumes', 'volumes_from', 'network_disabled',
            'entrypoint', 'cpu_shares', 'working_dir',
            'domainname', 'memswap_limit', 'host_config']

    for key in ctx.node.properties['params'].keys():
        if key in supported_params:
            d[key] = ctx.node.properties['params'].get(key)

    return d

def get_import_image_id(client, import_image_output):
    # It is useful beacause
    # import_image returns long string where in the second line
    # after last status is image id

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
