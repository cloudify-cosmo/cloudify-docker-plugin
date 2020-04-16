########
# Copyright (c) 2014-2020 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import json
import shutil
import getpass
import tempfile

from uuid import uuid1
from fabric.api import put, sudo

from .tasks import move_files
from .tasks import get_lan_ip
from .tasks import get_fabric_settings
from .tasks import get_docker_machine_from_ctx

from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from cloudify_common_sdk.resource_downloader import unzip_archive
from cloudify_common_sdk.resource_downloader import untar_archive
from cloudify_common_sdk.resource_downloader import get_shared_resource
from cloudify_common_sdk.resource_downloader import TAR_FILE_EXTENSTIONS

from .tasks import LOCAL_HOST_ADDRESSES


@operation
def prepare_terraform_files(ctx, **kwargs):

    docker_ip, docker_user, docker_key, container_volume = \
        get_docker_machine_from_ctx(ctx)

    source = \
        ctx.node.properties.get('resource_config', {}).get('source', "")
    backend = \
        ctx.node.properties.get('resource_config', {}).get('backend', {})
    variables = \
        ctx.node.properties.get('resource_config', {}).get('variables', {})
    environment_variables = \
        ctx.node.properties.get('resource_config', {}).get(
            'environment_variables', {})

    terraform_plugins = ctx.node.properties.get('terraform_plugins', [])

    if not source:
        raise NonRecoverableError("Please check the source value")
        return

    destination = tempfile.mkdtemp()

    # handle the provided source
    source_tmp_path = get_shared_resource(source)
    if source_tmp_path == source:
        # didn't download anything so check the provided path
        # if file and relative path to download from blueprint
        if os.path.isfile(source_tmp_path) and \
                not os.path.isabs(source_tmp_path):
            source_tmp_path = ctx.download_resource(source)
        # check file type if archived
        file_name = source_tmp_path.rsplit('/', 1)[1]
        file_type = file_name.rsplit('.', 1)[1]
        if file_type == 'zip':
            source_tmp_path = \
                unzip_archive(source_tmp_path)
        elif file_type in TAR_FILE_EXTENSTIONS:
            source_tmp_path = \
                untar_archive(source_tmp_path)

    storage_dir = "{0}/{1}".format(destination, "storage")
    os.mkdir(storage_dir)

    move_files(source_tmp_path, storage_dir)
    shutil.rmtree(source_tmp_path)

    storage_dir_prop = storage_dir.replace(destination, container_volume)
    ctx.instance.runtime_properties['storage_dir'] = storage_dir_prop

    plugins_dir = "{0}/{1}".format(destination, "plugins")
    os.mkdir(plugins_dir)

    backend_file = ""
    if backend:
        if not backend.get("name", ""):
            raise NonRecoverableError(
                "Check backend {0} name value".format(backend))
        backend_str = """
            terraform {
                backend "{backend_name}" {
                    {backend_options}
                }
            }
        """
        backend_options = ""
        for option_name, option_value in \
                backend.get("options", {}).items():
            if isinstance(option_value, basestring):
                backend_options += "{0} = \"{1}\"".format(option_name,
                                                          option_value)
            else:
                backend_options += "{0} = {1}".format(option_name,
                                                      option_value)
        backend_str.format(
            backend_name=backend.get("name"),
            backend_options=backend_options)
        backend_file = os.path.join(storage_dir, '{0}.tf'.format(
            backend.get("name")))
        with open(backend_file, 'w') as outfile:
            outfile.write(backend_str)
        # store the runtime property relative to container
        # rather than docker machine path
        backend_file = \
            backend_file.replace(destination, container_volume)
        ctx.instance.runtime_properties['backend_file'] = backend_file

    variables_file = ""
    if variables:
        variables_file = os.path.join(storage_dir, 'vars.json')
        with open(variables_file, 'w') as outfile:
            json.dump(variables, outfile)
        # store the runtime property relative to container
        # rather than docker machine path
        variables_file = \
            variables_file.replace(destination, container_volume)
        ctx.instance.runtime_properties['variables_file'] = variables_file
    ctx.instance.runtime_properties['environment_variables'] = \
        environment_variables
    if terraform_plugins:
        for plugin in terraform_plugins:
            downloaded_plugin_path = get_shared_resource(plugin)
            if downloaded_plugin_path == plugin:
                # it means we didn't download anything/ extracted
                raise NonRecoverableError(
                    "Check Plugin {0} URL".format(plugin))
            else:
                move_files(downloaded_plugin_path, plugins_dir, 0o775)
        os.chmod(plugins_dir, 0o775)
    plugins_dir = plugins_dir.replace(destination, container_volume)
    ctx.instance.runtime_properties['plugins_dir'] = plugins_dir

    # handle terraform scripts inside shell script
    terraform_script_file = os.path.join(storage_dir, '{0}.sh'.format(
        str(uuid1())))
    terraform_script = """#!/bin/bash -e
terraform init -no-color {backend_file} -plugin-dir={plugins_dir} {storage_dir}
terraform plan -no-color {vars_file} {storage_dir}
terraform apply -no-color -auto-approve {vars_file} {storage_dir}
terraform refresh -no-color {vars_file}
terraform state pull
    """.format(backend_file="" if not backend_file
               else "-backend-config={0}".format(backend_file),
               plugins_dir=plugins_dir,
               storage_dir=storage_dir_prop,
               vars_file="" if not variables
                            else " -var-file {0}".format(variables_file))
    ctx.logger.info("terraform_script_file content {0}".format(
        terraform_script))
    with open(terraform_script_file, 'w') as outfile:
        outfile.write(terraform_script)
    # store the runtime property relative to container
    # rather than docker machine path
    terraform_script_file = \
        terraform_script_file.replace(destination, container_volume)
    ctx.instance.runtime_properties['terraform_script_file'] = \
        terraform_script_file
    ctx.instance.runtime_properties['terraform_container_command_arg'] = \
        "bash {0}".format(terraform_script_file)

    # Reaching this point means we now have everything in this destination
    ctx.instance.runtime_properties['destination'] = destination
    ctx.instance.runtime_properties['docker_host'] = docker_ip
    # copy these files to docker machine if needed at that destination
    if docker_ip not in LOCAL_HOST_ADDRESSES and not docker_ip == get_lan_ip():
        with get_fabric_settings(ctx, docker_ip,
                                 docker_user,
                                 docker_key) as s:
            with s:
                destination_parent = destination.rsplit('/', 1)[0]
                if destination_parent != '/tmp':
                    sudo('mkdir -p {0}'.format(destination_parent))
                    sudo("chown -R {0}:{0} {1}".format(docker_user,
                                                       destination_parent))
                put(destination, destination_parent, mirror_local_mode=True)


@operation
def remove_terraform_files(ctx, **kwargs):

    docker_ip, docker_user, docker_key, _ = get_docker_machine_from_ctx(ctx)

    destination = ctx.instance.runtime_properties.get('destination', "")
    if not destination:
        raise NonRecoverableError("destination was not assigned due to error")
        return

    ctx.logger.info("removing file from destination {0}".format(destination))
    if os.path.exists(destination):
        os.system("sudo chown -R {0} {1}".format(getpass.getuser(),
                                                 destination))
        shutil.rmtree(destination)
        ctx.instance.runtime_properties.pop('destination', None)
    if not docker_ip:
        raise NonRecoverableError("no docker_ip was provided")
        return
    if docker_ip not in LOCAL_HOST_ADDRESSES and not docker_ip == get_lan_ip():
        with get_fabric_settings(ctx, docker_ip, docker_user, docker_key) as s:
            with s:
                sudo("rm -rf {0}".format(destination))
