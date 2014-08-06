import docker_plugin.subprocess_wrapper as subprocess_wrapper

from cloudify import exceptions


_DOCKER_INSTALLATION_CMD = 'install_docker.sh'
_MAX_WAITING_TIME = 10
_TIMEOUT_TERMINATE = 5


def install_docker(ctx):
    return_code, stdout, stderr = subprocess_wrapper.run_process(
        ctx,
        _DOCKER_INSTALLATION_CMD,
        waiting_for_output = _MAX_WAITING_TIME,
        timeout_terminate = _TIMEOUT_TERMINATE,
    )
    if stdout is not None:
        ctx.logger.debug('Docker installation stdout:\n{}'.format(stdout))
    if stderr is not None:
        ctx.logger.error(
            'Problems with docker installation, stderr:\n{}'.format(stderr)
        )
    if return_code != 0:
        raise exceptions.NonRecoverableError('Error during docker installation')
