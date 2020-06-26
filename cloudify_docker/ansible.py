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
import yaml
import json
import errno
import shutil
import getpass
import tempfile

from uuid import uuid1

from .tasks import get_lan_ip
from .tasks import get_fabric_settings
from .tasks import get_docker_machine_from_ctx

from cloudify.manager import get_rest_client
from cloudify.decorators import operation
from cloudify.exceptions import (NonRecoverableError, HttpException)

from cloudify_common_sdk.resource_downloader import unzip_archive
from cloudify_common_sdk.resource_downloader import untar_archive
from cloudify_common_sdk.resource_downloader import get_shared_resource
from cloudify_common_sdk.resource_downloader import TAR_FILE_EXTENSTIONS
from cloudify_common_sdk._compat import text_type

from .tasks import HOSTS
from .tasks import LOCAL_HOST_ADDRESSES
WORKSPACE = 'workspace'
LIST_TYPES = ['skip-tags', 'tags']
BP_INCLUDES_PATH = '/opt/manager/resources/blueprints/' \
                   '{tenant}/{blueprint}/{relative_path}'


@operation
def set_playbook_config(ctx, **kwargs):
    """
    Set all playbook node instance configuration as runtime properties
    :param _ctx: Cloudify node instance which is instance of CloudifyContext
    :param config: Playbook node configurations
    """
    def _get_secure_values(data, sensitive_keys, parent_hide=False):
        """
        ::param data : dict to check againt sensitive_keys
        ::param sensitive_keys : a list of keys we want to hide the values for
        ::param parent_hide : boolean flag to pass if the parent key is
                                in sensitive_keys
        """
        for key in data:
            # check if key or its parent {dict value} in sensitive_keys
            hide = parent_hide or (key in sensitive_keys)
            value = data[key]
            # handle dict value incase sensitive_keys was inside another key
            if isinstance(value, dict):
                # call _get_secure_value function recusivly
                # to handle the dict value
                inner_dict = _get_secure_values(value, sensitive_keys, hide)
                data[key] = inner_dict
            else:
                data[key] = '*'*len(value) if hide else value
        return data
    if kwargs and isinstance(kwargs, dict):
        kwargs = _get_secure_values(kwargs, kwargs.get("sensitive_keys", {}))
        for key, value in kwargs.items():
            ctx.instance.runtime_properties[key] = value
    ctx.instance.update()


@operation
def create_ansible_playbook(ctx, **kwargs):

    def handle_file_path(file_path, additional_playbook_files, _ctx):
        """Get the path to a file.

        I do this for two reasons:
          1. The Download Resource only downloads an individual file.
          Ansible Playbooks are often many files.
          2. I have not figured out how to pass a file as an in
          memory object to the PlaybookExecutor class.

        :param file_path: The `site_yaml_path` from `run`.
        :param additional_playbook_files: additional files
          adjacent to the playbook path.
        :param _ctx: The Cloudify Context.
        :return: The absolute path on the manager to the file.
        """

        def _get_deployment_blueprint(deployment_id):
            new_blueprint = ""
            try:
                # get the latest deployment update to get the new blueprint id
                client = get_rest_client()
                dep_upd = \
                    client.deployment_updates.list(deployment_id=deployment_id,
                                                   sort='created_at')[-1]
                new_blueprint = \
                    client.deployment_updates.get(dep_upd.id)[
                        "new_blueprint_id"]
            except KeyError:
                raise NonRecoverableError(
                    "can't get blueprint for deployment {0}".format(
                        deployment_id))
            return new_blueprint

        def download_nested_file_to_new_nested_temp_file(file_path, new_root,
                                                         _ctx):
            """ Download file to a similar folder system with a new
            root directory.

            :param file_path: the resource path for download resource source.
            :param new_root: Like a temporary directory
            :param _ctx:
            :return:
            """

            dirname, file_name = os.path.split(file_path)
            # Create the new directory path including the new root.
            new_dir = os.path.join(new_root, dirname)
            new_full_path = os.path.join(new_dir, file_name)
            try:
                os.makedirs(new_dir)
            except OSError as e:
                if e.errno == errno.EEXIST and os.path.isdir(new_dir):
                    pass
                else:
                    raise
            return _ctx.download_resource(file_path, new_full_path)

        if not isinstance(file_path, text_type):
            raise NonRecoverableError(
                'The variable file_path {0} is a {1},'
                'expected a string.'.format(file_path, type(file_path)))
        if not getattr(_ctx, '_local', False):
            if additional_playbook_files:
                # This section is intended to handle scenario where we want
                # to download the resource instead of use absolute path.
                # Perhaps this should replace the old way entirely.
                # For now, the important thing here is that we are
                # enabling downloading the playbook to a remote host.
                playbook_file_dir = tempfile.mkdtemp()
                new_file_path = download_nested_file_to_new_nested_temp_file(
                    file_path,
                    playbook_file_dir,
                    _ctx
                )
                for additional_file in additional_playbook_files:
                    download_nested_file_to_new_nested_temp_file(
                        additional_file,
                        playbook_file_dir,
                        _ctx
                    )
                return new_file_path
            else:
                # handle update deployment different blueprint playbook name
                deployment_blueprint = _ctx.blueprint.id
                if _ctx.workflow_id == 'update':
                    deployment_blueprint = \
                        _get_deployment_blueprint(_ctx.deployment.id)
                file_path = \
                    BP_INCLUDES_PATH.format(
                        tenant=_ctx.tenant_name,
                        blueprint=deployment_blueprint,
                        relative_path=file_path)
        if os.path.exists(file_path):
            return file_path
        raise NonRecoverableError(
            'File path {0} does not exist.'.format(file_path))

    def handle_site_yaml(site_yaml_path, additional_playbook_files, _ctx):
        """ Create an absolute local path to the site.yaml.

        :param site_yaml_path: Relative to the blueprint.
        :param additional_playbook_files: additional playbook files relative to
          the playbook.
        :param _ctx: The Cloudify context.
        :return: The final absolute path on the system to the site.yaml.
        """

        site_yaml_real_path = os.path.abspath(
            handle_file_path(site_yaml_path, additional_playbook_files, _ctx))
        site_yaml_real_dir = os.path.dirname(site_yaml_real_path)
        site_yaml_real_name = os.path.basename(site_yaml_real_path)
        site_yaml_new_dir = os.path.join(
            _ctx.instance.runtime_properties[WORKSPACE], 'playbook')
        shutil.copytree(site_yaml_real_dir, site_yaml_new_dir)
        site_yaml_final_path = os.path.join(site_yaml_new_dir,
                                            site_yaml_real_name)
        return site_yaml_final_path

    def get_inventory_file(filepath, _ctx, new_inventory_path):
        """
        This method will get the location for inventory file.
        The file location could be locally with relative to the blueprint
        resources or it could be remotely on the remote machine
        :return:
        :param filepath: File path to do check for
        :param _ctx: The Cloudify context.
        :param new_inventory_path: New path which holds the file inventory path
        when "filepath" is a local resource
        :return: File location for inventory file
        """
        if os.path.isfile(filepath):
            # The file already exists on the system, then return the file url
            return filepath
        else:
            # Check to see if the file does not exit, then try to lookup the
            # file from the Cloudify blueprint resources
            try:
                _ctx.download_resource(filepath, new_inventory_path)
            except HttpException:
                _ctx.logger.error(
                    'Error when trying to download {0}'.format(filepath))
                return None
            return new_inventory_path

    def handle_source_from_string(filepath, _ctx, new_inventory_path):
        inventory_file = get_inventory_file(filepath, _ctx, new_inventory_path)
        if inventory_file:
            return inventory_file
        else:
            with open(new_inventory_path, 'w') as outfile:
                _ctx.logger.info(
                    'Writing this data to temp file: {0}'.format(
                        new_inventory_path))
                outfile.write(filepath)
        return new_inventory_path

    def handle_key_data(_data, workspace_dir, container_volume):
        """Take Key Data from ansible_ssh_private_key_file and
        replace with a temp file.

        :param _data: The hosts dict (from YAML).
        :param workspace_dir: The temp dir where we are putting everything.
        :return: The hosts dict with a path to a temp file.
        """

        def recurse_dictionary(existing_dict,
                               key='ansible_ssh_private_key_file'):
            if key not in existing_dict:
                for k, v in existing_dict.items():
                    if isinstance(v, dict):
                        existing_dict[k] = recurse_dictionary(v)
            elif key in existing_dict:
                # If is_file_path is True, this has already been done.
                try:
                    is_file_path = os.path.exists(existing_dict[key])
                except TypeError:
                    is_file_path = False
                if not is_file_path:
                    private_key_file = \
                        os.path.join(workspace_dir, str(uuid1()))
                    with open(private_key_file, 'w') as outfile:
                        outfile.write(existing_dict[key])
                    os.chmod(private_key_file, 0o600)
                    private_key_file = \
                        private_key_file.replace(workspace_dir,
                                                 container_volume)
                    existing_dict[key] = private_key_file
            return existing_dict
        return recurse_dictionary(_data)

    def handle_sources(data, site_yaml_abspath, _ctx, container_volume):
        """Allow users to provide a path to a hosts file
        or to generate hosts dynamically,
        which is more comfortable for Cloudify users.

        :param data: Either a dict (from YAML)
            or a path to a conventional Ansible file.
        :param site_yaml_abspath: This is the path to the site yaml folder.
        :param _ctx: The Cloudify context.
        :return: The final path of the hosts file that
            was either provided or generated.
        """

        hosts_abspath = os.path.join(os.path.dirname(site_yaml_abspath), HOSTS)
        if isinstance(data, dict):
            data = handle_key_data(
                data, os.path.dirname(site_yaml_abspath), container_volume)
            if os.path.exists(hosts_abspath):
                _ctx.logger.error(
                    'Hosts data was provided but {0} already exists. '
                    'Overwriting existing file.'.format(hosts_abspath))
            with open(hosts_abspath, 'w') as outfile:
                yaml.safe_dump(data, outfile, default_flow_style=False)
        elif isinstance(data, text_type):
            hosts_abspath = handle_source_from_string(data, _ctx,
                                                      hosts_abspath)
        return hosts_abspath

    def prepare_options_config(options_config, run_data, destination, ctx):
        options_list = []
        if 'extra_vars' not in options_config:
            options_config['extra_vars'] = {}
        options_config['extra_vars'].update(run_data)
        for key, value in options_config.items():
            if key == 'extra_vars':
                f = tempfile.NamedTemporaryFile(delete=False, dir=destination)
                with open(f.name, 'w') as outfile:
                    json.dump(value, outfile)
                value = '@{filepath}'.format(filepath=f.name)
            elif key == 'verbosity':
                ctx.logger.error('No such option verbosity')
                del key
                continue
            key = key.replace("_", "-")
            if isinstance(value, text_type):
                value = value.encode('utf-8')
            elif isinstance(value, dict):
                value = json.dumps(value)
            elif isinstance(value, list) and key not in LIST_TYPES:
                value = [i.encode('utf-8') for i in value]
            elif isinstance(value, list):
                value = ",".join(value).encode('utf-8')
            options_list.append(
                '--{key}={value}'.format(key=key, value=repr(value)))
        return ' '.join(options_list)

    def prepare_playbook_args(ctx):
        playbook_source_path = \
            ctx.instance.runtime_properties.get('playbook_source_path', None)
        playbook_path = \
            ctx.instance.runtime_properties.get('playbook_path', None) \
            or ctx.instance.runtime_properties.get('site_yaml_path', None)
        sources = \
            ctx.instance.runtime_properties.get('sources', {})
        debug_level = \
            ctx.instance.runtime_properties.get('debug_level', 2)
        additional_args = \
            ctx.instance.runtime_properties.get('additional_args', '')
        additional_playbook_files = \
            ctx.instance.runtime_properties.get(
                'additional_playbook_files', None) or []
        ansible_env_vars = \
            ctx.instance.runtime_properties.get('ansible_env_vars', None) \
            or {'ANSIBLE_HOST_KEY_CHECKING': "False"}
        ctx.instance.runtime_properties[WORKSPACE] = tempfile.mkdtemp()
        # check if source path is provided [full path/URL]
        if playbook_source_path:
            # here we will combine playbook_source_path with playbook_path
            playbook_tmp_path = get_shared_resource(playbook_source_path)
            if playbook_tmp_path == playbook_source_path:
                # didn't download anything so check the provided path
                # if file and absolute path
                if os.path.isfile(playbook_tmp_path) and \
                        os.path.isabs(playbook_tmp_path):
                    # check file type if archived
                    file_name = playbook_tmp_path.rsplit('/', 1)[1]
                    file_type = file_name.rsplit('.', 1)[1]
                    if file_type == 'zip':
                        playbook_tmp_path = \
                            unzip_archive(playbook_tmp_path)
                    elif file_type in TAR_FILE_EXTENSTIONS:
                        playbook_tmp_path = \
                            untar_archive(playbook_tmp_path)
            playbook_path = "{0}/{1}".format(playbook_tmp_path,
                                             playbook_path)
        else:
            # here will handle the bundled ansible files
            playbook_path = handle_site_yaml(
                playbook_path, additional_playbook_files, ctx)
        playbook_args = {
            'playbook_path': playbook_path,
            'sources': handle_sources(sources, playbook_path,
                                      ctx,
                                      ctx.node.properties.get(
                                        'docker_machine', {}).get(
                                        'container_volume', "")),
            'verbosity': debug_level,
            'additional_args': additional_args or '',
        }
        options_config = \
            ctx.instance.runtime_properties.get('options_config', {})
        run_data = \
            ctx.instance.runtime_properties.get('run_data', {})
        return playbook_args, ansible_env_vars, options_config, run_data

    playbook_args, ansible_env_vars, options_config, run_data = \
        prepare_playbook_args(ctx)
    docker_ip, docker_user, docker_key, container_volume = \
        get_docker_machine_from_ctx(ctx)
    # The decorators will take care of creating the playbook workspace
    # which will package everything in a directory for our usages
    # it will be in the kwargs [playbook_args.playbook_path]
    playbook_path = playbook_args.get("playbook_path", "")
    debug_level = playbook_args.get("debug_level", 2)
    destination = os.path.dirname(playbook_path)
    verbosity = '-v'
    for i in range(1, debug_level):
        verbosity += 'v'
    command_options = \
        prepare_options_config(options_config, run_data, destination, ctx)
    additional_args = playbook_args.get("additional_args", "")
    if not destination:
        raise NonRecoverableError(
            "something is wrong with the playbook provided")
        return
    else:
        ctx.logger.info("playbook is ready at {0}".format(destination))
        playbook_path = playbook_path.replace(destination, container_volume)
        command_options = command_options.replace(destination,
                                                  container_volume)
        ctx.instance.runtime_properties['destination'] = destination
        ctx.instance.runtime_properties['docker_host'] = docker_ip
        ctx.instance.runtime_properties['ansible_env_vars'] = ansible_env_vars
        ctx.instance.runtime_properties['ansible_container_command_arg'] = \
            "ansible-playbook {0} -i hosts {1} {2} {3} ".format(
                verbosity,
                command_options,
                additional_args,
                playbook_path)
    # copy these files to docker machine if needed at that destination
    if not docker_ip:
        raise NonRecoverableError("no docker_ip was provided")
        return
    if docker_ip not in LOCAL_HOST_ADDRESSES and not docker_ip == get_lan_ip():
        with get_fabric_settings(ctx, docker_ip,
                                 docker_user,
                                 docker_key) as s:
            with s:
                destination_parent = destination.rsplit('/', 1)[0]
                if destination_parent != '/tmp':
                    s.sudo('mkdir -p {0}'.format(destination_parent))
                    s.sudo("chown -R {0}:{0} {1}".format(docker_user,
                                                destination_parent))
                s.put(destination, destination_parent, mirror_local_mode=True)


@operation
def remove_ansible_playbook(ctx, **kwargs):

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
                s.sudo("rm -rf {0}".format(destination))
