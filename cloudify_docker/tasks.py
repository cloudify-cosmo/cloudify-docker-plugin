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
import io
import os
import time
import json
import yaml
import fcntl
import fabric
import struct
import socket
import shutil
import getpass
import tarfile
import tempfile
import traceback
import subprocess

import docker

from uuid import uuid1
import patchwork.transfers
from functools import wraps
from contextlib import contextmanager

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from cloudify_common_sdk.resource_downloader import unzip_archive
from cloudify_common_sdk.resource_downloader import untar_archive
from cloudify_common_sdk.resource_downloader import get_shared_resource
from cloudify_common_sdk.resource_downloader import TAR_FILE_EXTENSTIONS
from cloudify_common_sdk._compat import text_type, PY2
from docker.errors import ImageNotFound, NotFound

try:
    if PY2:
        from fabric.api import settings, sudo, put
        FABRIC_VER = 1
    else:
        from fabric import Connection, Config
        FABRIC_VER = 2
except (ImportError, BaseException):
    FABRIC_VER = 'unclear'

from .constants import (HOSTS,
                        PLAYBOOK_PATH,
                        REDHAT_OS_VERS,
                        DEBIAN_OS_VERS,
                        HOSTS_FILE_NAME,
                        CONTAINER_VOLUME,
                        ANSIBLE_PRIVATE_KEY,
                        LOCAL_HOST_ADDRESSES)


def call_sudo(command, fab_ctx=None):
    ctx.logger.debug('Executing: {0}'.format(command))
    if FABRIC_VER == 2:
        out = fab_ctx.sudo(command)
        ctx.logger.debug('Out: {0}'.format(out))
        return out
    elif FABRIC_VER == 1:
        return sudo(command)


def call_put(destination,
             destination_parent,
             mirror_local_mode=None,
             fab_ctx=None):
    ctx.logger.debug('Copying: {0} {1}'.format(destination,
                                               destination_parent))
    if FABRIC_VER == 2:
        return patchwork.transfers.rsync(
            fab_ctx, destination, destination_parent, exclude='.git',
            strict_host_keys=False)
    elif FABRIC_VER == 1:
        return put(destination, destination_parent, mirror_local_mode)


def get_lan_ip():

    def get_interface_ip(ifname):
        if os.name != "nt":
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            return socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', bytes(ifname[:15]))
                # Python 3: add 'utf-8' to bytes
            )[20:24])
        return "127.0.0.1"

    try:
        ip = socket.gethostbyname(socket.gethostname())
        if ip.startswith("127.") and os.name != "nt":
            interfaces = ["eth0", "eth1", "eth2", "wlan0", "wlan1", "wifi0",
                          "ath0", "ath1", "ppp0"]
            for ifname in interfaces:
                try:
                    ip = get_interface_ip(ifname)
                    break
                except IOError:
                    pass
        return ip
    except socket.gaierror:
        return "127.0.0.1"  # considering no IP is configured to begin with


def is_remote_docker(docker_ip):
    return docker_ip and docker_ip not in LOCAL_HOST_ADDRESSES and \
        not (docker_ip == get_lan_ip())


def get_from_resource_config(*args):
    # takes the resource config , and whatever else you want to get from it
    # will be returned as a list and you handle it from the calling method
    #  i.e : source, dst = get_from_resource_config(res_config, 'src', 'dst')
    resource_config = args[0]
    result = []
    for arg in args[1:]:
        item = resource_config.get(arg)
        result.append(item)
    return result


@contextmanager
def get_fabric_settings(ctx, server_ip, server_user, server_private_key):
    if FABRIC_VER == 2:
        ctx.logger.info(
            "Fabric version : {0}".format(fabric.__version__))
    elif FABRIC_VER == 1:
        ctx.logger.info(
            "Fabric version : {0}".format(fabric.version.get_version()))
    try:
        is_file_path = os.path.exists(server_private_key)
    except TypeError:
        is_file_path = False
    if not is_file_path:
        private_key_file = os.path.join(
            tempfile.mkdtemp(), "{0}.pem".format(str(uuid1())))
        with open(private_key_file, 'w') as outfile:
            outfile.write(server_private_key)
        os.chmod(private_key_file, 0o400)
        server_private_key = private_key_file
    try:
        ctx.logger.debug("ssh connection to {0}@{1}".format(server_user,
                                                            server_ip))
        ctx.logger.debug("server_private_key {0} there? {1}".format(
            server_private_key, os.path.isfile(server_private_key)))
        if FABRIC_VER == 2:
            yield Connection(
                host=server_ip,
                connect_kwargs={
                    "key_filename": server_private_key
                },
                user=server_user,
                config=Config(
                    overrides={
                        "run": {
                            "warn": True
                        }}))
        elif FABRIC_VER == 1:
            yield settings(
                connection_attempts=5,
                disable_known_hosts=True,
                warn_only=True,
                host_string=server_ip,
                key_filename=server_private_key,
                user=server_user)
    finally:
        ctx.logger.info("Terminating ssh connection to {0}".format(server_ip))
        if not is_file_path:
            os.remove(server_private_key)
            shutil.rmtree(os.path.dirname(server_private_key))


def get_docker_machine_from_ctx(ctx):
    resource_config = ctx.node.properties.get('resource_config', {})
    docker_machine = ctx.node.properties.get('docker_machine', {})
    if docker_machine:  # takes precedence
        docker_ip = docker_machine.get('docker_ip', "")
        docker_user = docker_machine.get('docker_user', "")
        docker_key = docker_machine.get('docker_key', "")
        container_volume = docker_machine.get('container_volume', "")
    elif resource_config:
        # taking properties from resource_config
        docker_machine = resource_config.get('docker_machine', {})
        docker_ip = docker_machine.get('docker_ip', "")
        docker_user = docker_machine.get('docker_user', "")
        docker_key = docker_machine.get('docker_key', "")
        container_volume = docker_machine.get('container_volume', "")
    return docker_ip, docker_user, docker_key, container_volume


def handle_docker_exception(func):
    @wraps(func)
    def f(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except docker.errors.APIError as ae:
            raise NonRecoverableError(str(ae))
        except docker.errors.DockerException as de:
            raise NonRecoverableError(str(de))
        except Exception:
            tb = traceback.format_exc()
            ctx.logger.error("Exception Happend: {0}".format(tb))
            raise NonRecoverableError(tb)
    return f


def with_docker(func):
    @wraps(func)
    def f(*args, **kwargs):
        ctx = kwargs['ctx']
        client_config = ctx.node.properties.get('client_config', {})
        base_url = None
        if client_config.get('docker_host', '') \
                and client_config.get('docker_rest_port', ''):
            base_url = "tcp://{0}:{1}".format(
                client_config['docker_host'],
                client_config['docker_rest_port'])
        elif client_config.get('docker_sock_file', ''):
            base_url = "unix:/{0}".format(client_config['docker_sock_file'])
        else:
            # if we are here that means we don't have a valid docker config
            raise NonRecoverableError('Invalid docker client config')
        kwargs['docker_client'] = docker.DockerClient(base_url=base_url,
                                                      tls=False)
        return func(*args, **kwargs)
    return f


@handle_docker_exception
def follow_container_logs(ctx, docker_client, container, **kwargs):

    @handle_docker_exception
    def check_container_exited(docker_client, container):
        result = docker_client.containers.get(container.id)
        if result.status == 'exited':
            ctx.logger.info('Container exit_code {0}'.format(
                result.attrs['State']['ExitCode']))
            return True
        return False

    run_output = ""
    container_logs = container.logs(stream=True)
    ctx.logger.debug("Following container {0} logs".format(container))
    ctx.logger.debug("Attach returned {0}".format(container_logs))
    while True:
        try:
            chunk = next(container_logs)
            if chunk:
                chunk = chunk.decode('utf-8', 'replace').strip()
                run_output += "{0}\n".format(chunk)
                # ctx.logger.debug("{0}".format(chunk))
            elif check_container_exited(docker_client, container):
                break
        except StopIteration:
            break
    container_logs.close()
    return run_output


def move_files(source, destination, permissions=None):
    # let's handle folder vs file
    if os.path.isdir(source):
        for filename in os.listdir(source):
            if destination == os.path.join(source, filename):
                # moving files from parent to child case
                # so skip
                continue
            shutil.move(os.path.join(source, filename),
                        os.path.join(destination, filename))
            if permissions:
                os.chmod(os.path.join(destination, filename), permissions)
    else:
        shutil.move(source, destination)


@operation
def prepare_container_files(ctx, **kwargs):

    docker_ip, docker_user, docker_key, _ = get_docker_machine_from_ctx(ctx)
    resource_config = ctx.node.properties.get('resource_config', {})
    source, destination, extra_files, ansible_sources, terraform_sources = \
        get_from_resource_config(resource_config,
                                 'source',
                                 'destination',
                                 'extra_files',
                                 'ansible_sources',
                                 'terraform_sources')
    # check source to handle various cases [zip,tar,git]
    source_tmp_path = get_shared_resource(source)
    # check if we actually downloaded something or not
    delete_tmp = False
    if source_tmp_path == source:
        # didn't download anything so check the provided path
        # if file and absolute path or not
        if not os.path.isabs(source_tmp_path):
            # bundled and need to be downloaded from blurprint
            source_tmp_path = ctx.download_resource(source_tmp_path)
            delete_tmp = True
        if os.path.isfile(source_tmp_path):
            file_name = source_tmp_path.rsplit('/', 1)[1]
            file_type = file_name.rsplit('.', 1)[1]
            # check type
            if file_type == 'zip':
                unzipped_source = unzip_archive(source_tmp_path, False)
                if delete_tmp:
                    shutil.rmtree(os.path.dirname(source_tmp_path))
                source_tmp_path = unzipped_source
            elif file_type in TAR_FILE_EXTENSTIONS:
                unzipped_source = untar_archive(source_tmp_path, False)
                if delete_tmp:
                    shutil.rmtree(os.path.dirname(source_tmp_path))
                source_tmp_path = unzipped_source

    # Reaching this point we should have got the files into source_tmp_path
    if not destination:
        destination = tempfile.mkdtemp()
        # fix permissions for this temp directory
        os.chmod(destination, 0o755)
    move_files(source_tmp_path, destination)
    if os.path.isdir(source_tmp_path):
        shutil.rmtree(source_tmp_path)
    elif os.path.isfile(source_tmp_path):
        os.remove(source_tmp_path)

    # copy extra files to destination
    for file in (extra_files or []):
        try:
            is_file_path = os.path.exists(file)
            if is_file_path:
                shutil.copy(file, destination)
        except TypeError:
            raise NonRecoverableError("file {0} can't be copied".format(file))

    # handle ansible_sources -Special Case-:
    if ansible_sources:
        hosts_file = os.path.join(destination, HOSTS_FILE_NAME)
        # handle the private key logic
        private_key_val = ansible_sources.get(ANSIBLE_PRIVATE_KEY, "")
        if private_key_val:
            try:
                is_file_path = os.path.exists(private_key_val)
            except TypeError:
                is_file_path = False
            if not is_file_path:
                private_key_file = os.path.join(destination, str(uuid1()))
                with open(private_key_file, 'w') as outfile:
                    outfile.write(private_key_val)
                os.chmod(private_key_file, 0o600)
                ansible_sources.update({ANSIBLE_PRIVATE_KEY: private_key_file})
        # check if playbook_path was provided or not
        playbook_path = ansible_sources.get(PLAYBOOK_PATH, "")
        if not playbook_path:
            raise NonRecoverableError(
                "Check Ansible Sources, No playbook path was provided")
        hosts_dict = {
            "all": {
                "hosts": {
                    "instance": {}
                }
            }
        }
        for key in ansible_sources:
            if key in (CONTAINER_VOLUME, PLAYBOOK_PATH):
                continue
            elif key == ANSIBLE_PRIVATE_KEY:
                # replace docker mapping to container volume
                hosts_dict['all'][HOSTS]['instance'][key] = \
                    ansible_sources.get(key).replace(destination,
                                                     ansible_sources.get(
                                                        CONTAINER_VOLUME))
            else:
                hosts_dict['all'][HOSTS]['instance'][key] = \
                    ansible_sources.get(key)
        with open(hosts_file, 'w') as outfile:
            yaml.safe_dump(hosts_dict, outfile, default_flow_style=False)
        ctx.instance.runtime_properties['ansible_container_command_arg'] = \
            "ansible-playbook -i hosts {0}".format(playbook_path)

    # handle terraform_sources -Special Case-:
    if terraform_sources:
        container_volume = terraform_sources.get(CONTAINER_VOLUME, "")
        # handle files
        storage_dir = terraform_sources.get("storage_dir", "")
        if not storage_dir:
            storage_dir = os.path.join(destination, str(uuid1()))
        else:
            storage_dir = os.path.join(destination, storage_dir)
        os.mkdir(storage_dir)
        # move the downloaded files from source to storage_dir
        move_files(destination, storage_dir)
        # store the runtime property relative to container rather than docker
        storage_dir_prop = storage_dir.replace(destination, container_volume)
        ctx.instance.runtime_properties['storage_dir'] = storage_dir_prop

        # handle plugins
        plugins_dir = terraform_sources.get("plugins_dir", "")
        if not plugins_dir:
            plugins_dir = os.path.join(destination, str(uuid1()))
        else:
            plugins_dir = os.path.join(destination, plugins_dir)
        plugins = terraform_sources.get("plugins", {})
        os.mkdir(plugins_dir)
        for plugin in plugins:
            downloaded_plugin_path = get_shared_resource(plugin)
            if downloaded_plugin_path == plugin:
                # it means we didn't download anything/ extracted
                raise NonRecoverableError(
                    "Check Plugin {0} URL".format(plugin))
            else:
                move_files(downloaded_plugin_path, plugins_dir, 0o775)
        os.chmod(plugins_dir, 0o775)
        # store the runtime property relative to container rather than docker
        plugins_dir = plugins_dir.replace(destination, container_volume)
        ctx.instance.runtime_properties['plugins_dir'] = plugins_dir

        # handle variables
        terraform_variables = terraform_sources.get("variables", {})
        if terraform_variables:
            variables_file = os.path.join(storage_dir, 'vars.json')
            with open(variables_file, 'w') as outfile:
                json.dump(terraform_variables, outfile)
            # store the runtime property relative to container
            # rather than docker
            variables_file = \
                variables_file.replace(destination, container_volume)
            ctx.instance.runtime_properties['variables_file'] = variables_file

        # handle backend
        backend_file = ""
        terraform_backend = terraform_sources.get("backend", {})
        if terraform_backend:
            if not terraform_backend.get("name", ""):
                raise NonRecoverableError(
                    "Check backend {0} name value".format(terraform_backend))
            backend_str = """
                terraform {
                    backend "{backend_name}" {
                        {backend_options}
                    }
                }
            """
            backend_options = ""
            for option_name, option_value in \
                    terraform_backend.get("options", {}).items():
                if isinstance(option_value, text_type):
                    backend_options += "{0} = \"{1}\"".format(option_name,
                                                              option_value)
                else:
                    backend_options += "{0} = {1}".format(option_name,
                                                          option_value)
            backend_str.format(
                backend_name=terraform_backend.get("name"),
                backend_options=backend_options)
            backend_file = os.path.join(storage_dir, '{0}.tf'.format(
                terraform_backend.get("name")))
            with open(backend_file, 'w') as outfile:
                outfile.write(backend_str)
            # store the runtime property relative to container
            # rather than docker
            backend_file = \
                backend_file.replace(destination, container_volume)
            ctx.instance.runtime_properties['backend_file'] = backend_file

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
                   vars_file="" if not terraform_variables
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
    if is_remote_docker(docker_ip):
        with get_fabric_settings(ctx, docker_ip,
                                 docker_user,
                                 docker_key) as s:
            with s:
                destination_parent = destination.rsplit('/', 1)[0]
                if destination_parent != '/tmp':
                    call_sudo('mkdir -p {0}'.format(
                        destination_parent), fab_ctx=s)
                    call_sudo(
                        "chown -R {0}:{0} {1}".format(
                            docker_user, destination_parent),
                        fab_ctx=s)
                call_put(
                    destination,
                    destination_parent,
                    mirror_local_mode=True,
                    fab_ctx=s)


@operation
def remove_container_files(ctx, **kwargs):

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
    ctx.instance.runtime_properties.pop('destination', None)
    if is_remote_docker(docker_ip):
        with get_fabric_settings(ctx, docker_ip, docker_user, docker_key) as s:
            with s:
                call_sudo("rm -rf {0}".format(destination), fab_ctx=s)


@operation
@handle_docker_exception
@with_docker
def list_images(ctx, docker_client, **kwargs):
    ctx.instance.runtime_properties['images'] = \
        docker_client.images.list(all=True)


@operation
@handle_docker_exception
def install_docker(ctx, **kwargs):
    # fetch the data needed for installation
    docker_ip, docker_user, docker_key, _ = get_docker_machine_from_ctx(ctx)
    resource_config = ctx.node.properties.get('resource_config', {})
    install_url = resource_config.get('install_url')
    post_install_url = resource_config.get('install_script')

    if not (install_url and post_install_url):
        raise NonRecoverableError("Please validate your install config")

    with get_fabric_settings(ctx, docker_ip, docker_user, docker_key) as s:
        with s:
            call_sudo(
                'curl -fsSL {0} -o /tmp/install.sh'.format(install_url),
                fab_ctx=s)
            call_sudo('chmod 0755 /tmp/install.sh', fab_ctx=s)
            call_sudo('sh /tmp/install.sh', fab_ctx=s)
            call_sudo(
                'curl -fsSL {0} -o /tmp/postinstall.sh'.format(
                    post_install_url),
                fab_ctx=s)
            call_sudo('chmod 0755 /tmp/postinstall.sh', fab_ctx=s)
            call_sudo('sh /tmp/postinstall.sh', fab_ctx=s)
            call_sudo('usermod -aG docker {0}'.format(docker_user), fab_ctx=s)


@operation
def uninstall_docker(ctx, **kwargs):
    # fetch the data needed for installation
    docker_ip, docker_user, docker_key, _ = get_docker_machine_from_ctx(ctx)
    with get_fabric_settings(ctx, docker_ip, docker_user, docker_key) as s:
        with s:
            os_type = call_sudo("echo $(python -c "
                                "'import platform; "
                                "print(platform.linux_distribution("
                                "full_distribution_name=False)[0])')",
                                fab_ctx=s)
            if not PY2:
                os_type = os_type.stdout
            os_type = os_type.splitlines()
            value = ""
            # sometimes ubuntu print the message when using sudo
            for line in os_type:
                if "unable to resolve host" in line:
                    continue
                else:
                    value += line
            os_type = value.strip()
            ctx.logger.info("os_type {0}".format(os_type))
            result = ""
            if os_type.lower() in REDHAT_OS_VERS:
                result = call_sudo("yum remove -y docker*", fab_ctx=s)
            elif os_type.lower() in DEBIAN_OS_VERS:
                result = call_sudo("apt-get remove -y docker*", fab_ctx=s)
            ctx.logger.info("uninstall result {0}".format(result))


@operation
@handle_docker_exception
@with_docker
def list_host_details(ctx, docker_client, **kwargs):
    ctx.instance.runtime_properties['host_details'] = docker_client.info()


@operation
@handle_docker_exception
@with_docker
def list_containers(ctx, docker_client, **kwargs):
    ctx.instance.runtime_properties['contianers'] = \
        docker_client.containers.list(all=True, trunc=True)


@operation
@handle_docker_exception
@with_docker
def pull_image(ctx, docker_client, **kwargs):
    resource_config = ctx.node.properties.get('resource_config', {})
    tag = resource_config.get('tag')
    all_tags = resource_config.get('all_tags', False)
    if not tag:
        return
    repository = tag.split(':')[0]
    try:
        image_tag = tag.split(':')[1]
    except IndexError:
        image_tag = 'latest'
    try:
        docker_client.images.get(tag)
    except ImageNotFound:
        docker_client.images.pull(repository=repository,
                                  tag=image_tag, all_tags=all_tags)


@operation
@handle_docker_exception
@with_docker
def build_image(ctx, docker_client, **kwargs):
    resource_config = ctx.node.properties.get('resource_config', {})
    image_content, tag = get_from_resource_config(resource_config,
                                                  'image_content',
                                                  'tag')
    if image_content:
        # check what content we got, URL , path or string
        split = image_content.split('://')
        schema = split[0]
        if schema in ['http', 'https']:
            downloaded_image_content = get_shared_resource(image_content)
            with open(downloaded_image_content, "r") as f:
                image_content = f.read()
        elif os.path.isfile(image_content):
            if os.path.isabs(image_content):
                with open(image_content, "r") as f:
                    image_content = f.read()
            else:
                downloaded_image_content = ctx.download_resource(image_content)
                with open(downloaded_image_content, "r") as f:
                    image_content = f.read()
        else:
            ctx.logger.info("Building image with tag {0}".format(tag))
            # replace the new line str with new line char
            image_content = image_content.replace("\\n", '\n')
        ctx.logger.debug("Image Dockerfile:\n{0}".format(image_content))
        build_output = ""
        img_data = io.BytesIO(image_content.encode('ascii'))
        # the result of build will have a tuple (image_id, build_result)
        for chunk in docker_client.images.build(fileobj=img_data, tag=tag)[1]:
            build_output += "{0}\n".format(chunk)
        ctx.instance.runtime_properties['build_result'] = build_output
        ctx.logger.info("Build Output {0}".format(build_output))
        if 'errorDetail' in build_output:
            raise NonRecoverableError("Build Failed check build-result")
        ctx.instance.runtime_properties['image'] =  \
            repr(docker_client.images.get(name=tag))


@operation
@handle_docker_exception
@with_docker
def remove_image(ctx, docker_client, **kwargs):
    resource_config = ctx.node.properties.get('resource_config', {})
    tag = resource_config.get('tag', "")
    build_res = ctx.instance.runtime_properties.pop('build_result', "")
    if tag:
        if not build_res or 'errorDetail' in build_res:
            ctx.logger.info("build contained errors , nothing to do ")
            return
        ctx.logger.debug("Removing image with tag {0}".format(tag))
        remove_res = docker_client.images.remove(tag, force=True)
        ctx.logger.info("Remove result {0}".format(remove_res))


@operation
@handle_docker_exception
@with_docker
def create_container(ctx, docker_client, **kwargs):
    resource_config = ctx.node.properties.get('resource_config', {})
    image_tag, container_args = get_from_resource_config(resource_config,
                                                         'image_tag',
                                                         'container_args')
    if image_tag:
        ctx.logger.debug(
            "Running container from image tag {0}".format(image_tag))
        host_config = container_args.pop("host_config", {})

        # handle volume mapping
        # map each entry to it's volume based on index
        volumes = container_args.pop('volumes', None)
        if volumes:
            # logic was added to handle mapping to create_container
            paths_on_host = container_args.pop('volumes_mapping', None)
            binds_list = []
            if paths_on_host:
                for path, volume in zip(paths_on_host, volumes):
                    binds_list.append('{0}:{1}'.format(path, volume))
                host_config.update({"volumes": binds_list})
        ctx.logger.debug("host_config : {0}".format(host_config))
        container_args.update(host_config)
        ctx.instance.runtime_properties['container_args'] = container_args
        ctx.logger.debug("container_args : {0}".format(container_args))

        # docker create
        container = docker_client.containers.create(image=image_tag,
                                                    **container_args)
        # docker start
        container.start()

        # the run method will handle the lifecycle create,
        # start and logs in case of detach no logs
        # container = docker_client.containers.run(image=image_tag,
        #                                          **container_args)

        # if command in detach mode -since the command will keep running-
        # no need to follow logs [ it wil return the Container Object ]
        if container_args.get("detach", False):
            ctx.logger.info("command is running in detach mode True")
            ctx.instance.runtime_properties['container'] = container.id
            container_info = docker_client.containers.get(container.id)
            ctx.instance.runtime_properties['container_info'] = \
                repr(container_info)
            return
        ctx.logger.info("container was created : {0}".format(container))
        ctx.instance.runtime_properties['container'] = container.id
        container_logs = follow_container_logs(ctx, docker_client, container)
        ctx.logger.info("container logs : {0} ".format(container_logs))
        ctx.instance.runtime_properties['run_result'] = container_logs


@operation
@handle_docker_exception
@with_docker
def start_container(ctx, docker_client, **kwargs):
    resource_config = ctx.node.properties.get('resource_config', {})
    container_args = resource_config.get('container_args', {})
    container = ctx.instance.runtime_properties.get('container', "")
    if not container:
        ctx.logger.info("container was not create successfully, nothing to do")
        return
    if not container_args.get("command", ""):
        ctx.logger.info("no command sent to container, nothing to do")
        return
    ctx.logger.debug(
        "Running this command on container : {0} ".format(
            container_args.get("command", "")))
    container_obj = docker_client.containers.get(container)
    container_obj.start()
    container_logs = follow_container_logs(ctx, docker_client, container_obj)
    ctx.logger.info("container logs : {0} ".format(container_logs))
    ctx.instance.runtime_properties['run_result'] = container_logs


def check_if_applicable_command(command):
    EXCEPTION_LIST = ('terraform', 'ansible-playbook', 'ansible')
    # check if command given the platform ,
    # TODO : make it more dynamic
    # at least : bash , python , and basic unix commands ...
    # adding exceptions like terraform, ansible_playbook
    # if they are not installed on the host
    # can be extended based on needs
    if command in EXCEPTION_LIST:
        return True
    rc = subprocess.call(['which', command])
    if rc == 0:
        return True
    else:
        return False


def find_host_script_path(docker_client, container_id,
                          command, container_args):
    # given the original command and the mapping
    # let's return the path we will be overriding the content for
    script = None
    argument_list = command.split(' ', 1)[1].split()
    # weed out flags and stop on first argument after that
    # for example in ansible we would have :
    # ansible-playbook -i {hosts} {actual_file_we want}
    # flags trick to get the file and validate it is part of mapping
    skip_flag_arg = False
    for argument in argument_list:
        # skip the flags
        if argument.startswith('-'):
            skip_flag_arg = True
            continue
        if skip_flag_arg:
            skip_flag_arg = False
            continue
        script = argument
        break
    ctx.logger.debug("script to override {0}".format(script))
    # Handle the attached volume to override
    # the script with stop_command
    volumes = container_args.get("volumes", None)
    volumes_mapping = container_args.get("volumes_mapping", None)
    if volumes and volumes_mapping:
        # look for the script in the mapped volumes
        mapping_to_use = ""
        for volume, mapping in zip(volumes, volumes_mapping):
            ctx.logger.debug(
                "check if script {0} contain volume {1}".format(script,
                                                                volume))
            if volume in script:
                ctx.logger.debug("replacing {0} with {1}".format(volume,
                                                                 mapping))
                script = script.replace(volume, mapping)
                ctx.logger.debug("script to modify is {0}".format(script))
                mapping_to_use = mapping
                break

        if not mapping_to_use:
            ctx.logger.info("volume mapping is not correct")
            return
    else:
        # let's look for local files inside the container
        containerObj = docker_client.containers.get(container_id)
        bits, stats = containerObj.get_archive(script)
        if stats.get('size', 0) > 0:
            destination = tempfile.mkdtemp()
            f = open(
                os.path.join(destination, stats.get('name')), 'wb')
            for chunk in bits:
                f.write(chunk)
            f.close()
            file_obj = tarfile.open(f.name, "r")
            file = file_obj.extractfile(stats.get('name'))
            file_content = file.read()
            file_obj.close()
            os.remove(f.name)
            # return the file name and content so it would be handled
            # via put_archive though cotinaer API
            return script, file_content
        else:
            ctx.logger.info('script not found inside the container '
                            'since no volumes were mapped')
            return
    return script


def handle_container_timed_out(ctx, docker_client, container_id,
                               container_args, stop_command):
    # check the original command in the properties
    command = container_args.get("command", "")
    if not command:
        ctx.logger.info("no command sent to container, nothing to do")
        return
    # assuming the container was passed : {script_executor} {script} [ARGS]
    if len(command.split(' ', 1)) >= 2:
        script_executor = command.split(' ', 1)[0]
        if not check_if_applicable_command(script_executor):
            ctx.logger.info(
                "can't run this command {0}".format(script_executor))
            return
        # we will get the docker_host conf from mapped
        # container_files node through relationships
        volumes = container_args.get("volumes", None)
        volumes_mapping = container_args.get("volumes_mapping", None)
        docker_ip = ""
        relationships = list(ctx.instance.relationships)
        if volumes and volumes_mapping:
            for rel in relationships:
                node = rel.target.node
                resource_config = node.properties.get('resource_config', {})
                docker_machine = resource_config.get('docker_machine', {})
                ctx.logger.debug("checking for IP in {0}".format(node.name))
                if node.type == 'cloudify.nodes.docker.container_files':
                    docker_ip = docker_machine.get('docker_ip', "")
                    docker_user = docker_machine.get('docker_user', "")
                    docker_key = docker_machine.get('docker_key', "")
                    break
                if node.type == 'cloudify.nodes.docker.terraform_module':
                    docker_machine = node.properties.get('docker_machine', {})
                    docker_ip = docker_machine.get('docker_ip', "")
                    docker_user = docker_machine.get('docker_user', "")
                    docker_key = docker_machine.get('docker_key', "")
                    break
            if not docker_ip:
                ctx.logger.info(
                    "can't find docker_ip in container_files "
                    "node through relationships")
                return

        # here we assume the command is OK , and we have arguments to it

        script, _ = find_host_script_path(docker_client, container_id,
                                          command, container_args)
        if not script:
            return
        replace_script = stop_command

        is_ansible_custom_case = 'ansible' in script_executor
        if is_ansible_custom_case:
            _, replace_script = find_host_script_path(docker_client,
                                                      container_id,
                                                      stop_command,
                                                      container_args)
            if not replace_script:
                return

            # check if we have volume mapping or not
            if volumes and volumes_mapping:
                # let's read from the remote docker if that is the case
                if is_remote_docker(docker_ip):
                    with get_fabric_settings(ctx, docker_ip, docker_user,
                                             docker_key) as s:
                        with s:
                            replace_script = call_sudo(
                                'cat {0}'.format(replace_script),
                                fab_ctx=s).stdout
                else:
                    # check from local
                    with open(replace_script, 'r') as f:
                        replace_script = f.read()

        container_obj = docker_client.containers.get(container_id)
        # if we are here , then we found the script
        # in one of the mapped volumes
        ctx.logger.debug("override script {0} content to {1}".format(
            script, replace_script))
        if volumes and volumes_mapping:
            with open(script, 'w') as outfile:
                outfile.write(replace_script)

            if is_remote_docker(docker_ip):
                with get_fabric_settings(ctx, docker_ip, docker_user,
                                         docker_key) as s:
                    with s:
                        call_put(
                            script, script, mirror_local_mode=True, fab_ctx=s)
        else:
            # if we are here we have the replace content and we need to replace
            # script content inside the container files
            script_dir = os.path.dirname("/{0}".format(script))
            pw_tarstream = io.BytesIO()
            pw_tar = tarfile.TarFile(fileobj=pw_tarstream, mode='w')
            file_data = replace_script
            tarinfo = tarfile.TarInfo(name=script)
            tarinfo.size = len(file_data)
            tarinfo.mtime = time.time()
            pw_tar.addfile(tarinfo, io.BytesIO(file_data))
            pw_tar.close()
            pw_tarstream.seek(0)
            container_obj.put_archive(script_dir,
                                      pw_tarstream)

        # now we can restart the container , and it will
        # run with the overriden script that contain the
        # stop_command
        container_obj.restart()
        container_logs = follow_container_logs(ctx, docker_client,
                                               container_obj)
        ctx.logger.info("container logs : {0} ".format(container_logs))
    else:
        ctx.logger.info("""can't send this command {0} to container,
since it is unreachable""".format(stop_command))
        return


@operation
@handle_docker_exception
@with_docker
def stop_container(ctx, docker_client, stop_command, **kwargs):
    container = ctx.instance.runtime_properties.get('container', "")
    resource_config = ctx.node.properties.get('resource_config', {})
    image_tag, container_args = get_from_resource_config(resource_config,
                                                         'image_tag',
                                                         'container_args')
    if not stop_command:
        ctx.logger.info("no stop command, nothing to do")
        try:
            container_obj = docker_client.containers.get(container)
            container_obj.stop()
            container_obj.wait()
        except NotFound:
            pass
        return

    script_executor = stop_command.split(' ', 1)[0]
    if not check_if_applicable_command(script_executor):
        ctx.logger.info(
            "can't run this command {0}".format(script_executor))
        return

    if container:
        ctx.logger.info(
            "Stop Contianer {0} from tag {1} with command {2}".format(
                container, image_tag, stop_command))
        # attach to container socket and send the stop_command
        container_obj = docker_client.containers.get(container)
        socket = container_obj.attach_socket(
            params={
                'stdin': 1,
                "stdout": 1,
                'stream': 1,
                "logs": 1
            })
        try:
            socket._sock.settimeout(20)
            socket._sock.send(stop_command.encode('utf-8'))
            buffer = ""
            while True:
                data = socket._sock.recv(4096)
                if not data:
                    break
                buffer += data.decode('utf-8')
            ctx.logger.info("Stop command result {0}".format(buffer))
        except docker.errors.APIError as ae:
            ctx.logger.error("APIError {0}".format(str(ae)))
        except Exception as e:
            message = e.message if hasattr(e, 'message') else e
            # response = e.response if hasattr(e, 'response') else e
            # explanation = e.explanation if hasattr(e, 'explanation') else e
            # errno = e.errno if hasattr(e, 'errno') else e
            ctx.logger.error("exception : {0}".format(message))
            # if timeout happened that means the container exited,
            # and if want to do something for the container,
            # or handle any special case if we want that
            if "timed out" in repr(message):
                ctx.logger.debug('Expected case since it is stopped '
                                 'and we want a chance to execute '
                                 'extra command with override to old one')
                # Special Handling for terraform -to call cleanup for example-
                # we can switch the command with stop_command and restart
                handle_container_timed_out(ctx, docker_client, container,
                                           container_args, stop_command)

        socket.close()
        container_obj.stop()
        container_obj.wait()


@operation
@handle_docker_exception
@with_docker
def remove_container(ctx, docker_client, **kwargs):
    container = ctx.instance.runtime_properties.get('container', "")
    resource_config = ctx.node.properties.get('resource_config', {})
    image_tag = resource_config.get('image_tag', "")
    if container:
        ctx.logger.info(
            "remove Contianer {0} from tag {1}".format(container,
                                                       image_tag))
        container_obj = docker_client.containers.get(container)
        remove_res = container_obj.remove()
        ctx.instance.runtime_properties.pop('container')
        ctx.logger.info("Remove result {0}".format(remove_res))
