import subprocess_wrapper

from cloudify import mocks


_PROCESS_COMMAND = 'install_docker.sh'


def launch_process(ctx):
    return_code, stdout, stderr = subprocess_wrapper.run_process(
        ctx,
        _PROCESS_COMMAND
    )
    ctx.logger.info('stdout\n{}'.format(stdout))
    ctx.logger.info('stderr\n{}'.format(stderr))
    assert(return_code == 0)
