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

# Cloudify Imports
from cloudify import ctx


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


def validate_container_ready(ctx):
    """ Checks the containers processes
        and makes sure the container is ready to be used
    """
    ctx.instance.runtime_properties['container_id']
