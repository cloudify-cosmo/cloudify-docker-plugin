import errno
import os
import psutil
import subprocess
import time
import fcntl

from cloudify import exceptions
from cloudify import mocks


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


def _read_streams(ctx, pipe, waiting_for_output):
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
            if time_no_output >= waiting_for_output:
                ctx.logger.error('Process hung up')
                hung_up = True
            else:
                time_no_output += 1
                time.sleep(1)
        else:
            time_no_output = 0
    ctx.logger.info('Read stdout, stderr')
    return stdout, stderr, not hung_up


def _set_flags(ctx, pipe):
    stdout_flags = fcntl.fcntl(pipe.stdout, fcntl.F_GETFL)
    fcntl.fcntl(pipe.stdout, fcntl.F_SETFL, stdout_flags | os.O_NONBLOCK)
    stderr_flags = fcntl.fcntl(pipe.stderr, fcntl.F_GETFL)
    fcntl.fcntl(pipe.stderr, fcntl.F_SETFL, stderr_flags | os.O_NONBLOCK)


def _get_simple_output(ctx, pipe, stream):
    end_of_output, wait_output, output = _get_output(ctx, pipe, stream)
    return output


def _manually_clean_up(ctx, pipe, timeout_terminate, waiting_for_output):
    ctx.logger.info('Terminating process')
    pipe.terminate()
    time_no_terminate = 0
    process = psutil.Process(pipe.pid)
    while (
            time_no_terminate < timeout_terminate and
            process.status() != psutil.STATUS_ZOMBIE
    ):
        time.sleep(1)
        process = psutil.Process(pipe.pid)
        time_no_terminate += 1

    stdout, stderr, success = _read_streams(ctx, pipe, waiting_for_output)
    if process.status() == psutil.STATUS_ZOMBIE:
        ctx.logger.info('Process terminated')
    else:
        ctx.logger.info('Killing process')
        pipe.kill()
        stdout += _get_simple_output(ctx, pipe, pipe.stdout)
        stderr += _get_simple_output(ctx, pipe, pipe.stderr)
    pipe.wait()
    return stdout, stderr


def _clean_up(ctx, pipe, success, timeout_terminate, waiting_for_output):
    ctx.logger.info('Cleaning up')
    stdout, stderr = '', ''
    if success:
        pipe.wait()
    else:
        stdout, stderr = _manually_clean_up(
            ctx,
            pipe,
            timeout_terminate,
            waiting_for_output
        )
    pipe.stdout.close()
    pipe.stderr.close()
    ctx.logger.info('Cleaned up')
    return stdout, stderr


def run_process(
        ctx,
        process,
        waiting_for_output,
        timeout_terminate
):
    ctx.logger.info('Starting process')
    pipe = subprocess.Popen(
        process.split(' '),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _set_flags(ctx, pipe)
    stdout, stderr, success = _read_streams(ctx, pipe, waiting_for_output)
    new_stdout, new_stderr = _clean_up(
        ctx,
        pipe,
        success,
        timeout_terminate,
        waiting_for_output
    )
    stdout += new_stdout
    stderr += new_stderr
    ctx.logger.info('Finishing process')
    return pipe.returncode, stdout, stderr
