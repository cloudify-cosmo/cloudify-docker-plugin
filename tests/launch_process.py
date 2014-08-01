import errno
import os
import psutil
import subprocess
import threading
import time
from fcntl import fcntl, F_GETFL, F_SETFL

from cloudify import exceptions
from cloudify import mocks


_PROCESS_COMMAND = './test_script.sh'
_MAX_WAITING_TIME = 5
_TIMEOUT_TERMINATE = 10


def _get_output(ctx, pipe, stream):
    end_of_output, wait_output = False, False
    output = ''
    try:
        out = stream.read()
    except IOError as e:
        if e.errno != errno.EAGAIN:
            ctx.logger.error(e)
            raise exceptions.NonRecoverableError(e)
        else:
            wait_output = True
    else:
        if not out:
            end_of_output = True
        else:
            output = out
    finally:
        return end_of_output, wait_output, output


def _read_streams(ctx, pipe):
    ctx.logger.info('Reading stdout, stderr')
    end_of_output, end_of_stdout, end_of_stderr = False, False, False
    time_no_output = 0
    stdout, stderr = '', ''
    hung_up = False
    while not end_of_output and not hung_up:
        if not end_of_stdout:
            end_of_stdout, wait_stdout, new_stdout = _get_output(
                ctx,
                pipe,
                pipe.stdout
            )
            stdout += new_stdout
        if not end_of_stderr:
            end_of_stderr, wait_stderr, new_stderr = _get_output(
                ctx,
                pipe,
                pipe.stderr
            )
            stderr += new_stderr
        end_of_output = end_of_stdout and end_of_stderr
        if (
                (not end_of_output) and
                (end_of_stdout or wait_stdout) and
                (end_of_stderr or wait_stderr)
        ):
            if time_no_output >= _MAX_WAITING_TIME:
                ctx.logger.error('Process {} hung up'.format(_PROCESS_COMMAND))
                hung_up = True
            else:
                time_no_output += 1
                time.sleep(1)
        else:
            time_no_output = 0
    ctx.logger.info('Read stdout, stderr')
    return stdout, stderr, not hung_up


def _set_flags(ctx, pipe):
    stdout_flags = fcntl(pipe.stdout, F_GETFL)
    fcntl(pipe.stdout, F_SETFL, stdout_flags | os.O_NONBLOCK)
    stderr_flags = fcntl(pipe.stderr, F_GETFL)
    fcntl(pipe.stderr, F_SETFL, stderr_flags | os.O_NONBLOCK)


def _manually_clean_up(ctx, pipe):
    ctx.logger.info('Terminating proccess {}'.format(_PROCESS_COMMAND))
    pipe.terminate()
    time_no_terminate = 0
    process = psutil.Process(pipe.pid)
    while (
            time_no_terminate < _TIMEOUT_TERMINATE and
            process.status() != psutil.STATUS_ZOMBIE
    ):
        time.sleep(1)
        process = psutil.Process(pipe.pid)
        time_no_terminate += 1
    ctx.logger.info('Killing proccess {}'.format(_PROCESS_COMMAND))
    pipe.kill()
    pipe.wait()


def _clean_up(ctx, pipe, success):
    ctx.logger.info('Cleaning up')
    if success:
        pipe.wait()
    else:
        _manually_clean_up(ctx, pipe)
    pipe.stdout.close()
    pipe.stderr.close()
    ctx.logger.info('Cleaned up')


def run_process(ctx):
    ctx.logger.info('Starting proccess {}'.format(_PROCESS_COMMAND))
    pipe = subprocess.Popen(
        [_PROCESS_COMMAND],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _set_flags(ctx, pipe)
    stdout, stderr, success = _read_streams(ctx, pipe)
    _clean_up(ctx, pipe, success)
    ctx.logger.info('Finishing proccess {}'.format(_PROCESS_COMMAND))
    return pipe.returncode, stdout, stderr


if __name__ == '__main__':
    ctx = mocks.MockCloudifyContext()
    run_process(ctx)
