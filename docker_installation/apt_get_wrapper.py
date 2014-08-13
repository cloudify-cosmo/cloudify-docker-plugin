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


import logging
import os

import docker_installation.resources as resources
import docker_installation.subprocess_wrapper as subprocess_wrapper


_DOCKER_INSTALLATION_CMD = [os.path.join(
    os.path.dirname(resources.__file__),
    "install_docker.sh"
)]
_MAX_WAITING_TIME = 10
_TIMEOUT_TERMINATE = 5


logging.basicConfig(level=logging.INFO)


def install_docker():
    return_code, stdout, stderr = subprocess_wrapper.run_process(
        _DOCKER_INSTALLATION_CMD,
        waiting_for_output=_MAX_WAITING_TIME,
        timeout_terminate=_TIMEOUT_TERMINATE
    )
    if stdout != '':
        logging.info(
            'Docker installation\'s stdout:\n{}\n'.format(stdout)
        )
    if return_code != 0:
        if stderr != '':
            logging.error(
                'Docker installation\'s stderr:\n{}\n'.format(stderr)
            )
        raise Exception(
            'Error during docker installation'
        )
