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


import errno
import fcntl
import os
import psutil
import select
import subprocess
import time


_DELAY_STEP = 1


def _set_ononblock(fd):
    curr_flags = fcntl.fcntl(fd.fileno(), fcntl.F_GETFL)
    fcntl.fcntl(
        fd.fileno(),
        fcntl.F_SETFL,
        curr_flags | os.O_NONBLOCK
    )


def _read_async(fd):
    output, eof = '', False
    try:
        output = fd.read()
    except IOError as e:
        if e.errno != errno.EAGAIN:
            raise
    else:
        eof = (output == '')
    return output, eof


def _read_fds(ctx, process, timeout):
    ctx.logger.info('Waiting for subprocess to finish...')
    fds = {
        process.stdout.fileno(): {
            'file': process.stdout,
            'output': '',
            'eof': False
        },
        process.stderr.fileno(): {
            'file': process.stderr,
            'output': '',
            'eof': False
        }
    }
    while True:
        read_fds, _, _ = select.select(
            [fds[fd]['file'] for fd in fds if not fds[fd]['eof']],
            [],
            [],
            timeout
        )
        if not read_fds:
            ctx.logger.error('Subprocess hung up')
            hung_up = True
            break
        for fd in read_fds:
            output, fds[fd.fileno()]['eof'] = _read_async(fd)
            fds[fd.fileno()]['output'] += output
        if all(fds[fd]['eof'] for fd in fds):
            ctx.logger.info('Subprocess finished')
            hung_up = False
            break
    return (
        fds[process.stdout.fileno()]['output'],
        fds[process.stderr.fileno()]['output'],
        not hung_up
    )


def _manually_clean_up(ctx, process, waiting_for_output, timeout_terminate):
    ctx.logger.info('Terminating process')
    process.terminate()
    time_no_terminate = 0
    p = psutil.Process(process.pid)
    while (
            time_no_terminate < timeout_terminate and
            p.status() != psutil.STATUS_ZOMBIE
    ):
        time.sleep(_DELAY_STEP)
        time_no_terminate += 1
        p = psutil.Process(process.pid)

    stdout, stderr, success = _read_fds(ctx, process, waiting_for_output)
    if p.status() == psutil.STATUS_ZOMBIE:
        ctx.logger.info('Process terminated')
    else:
        ctx.logger.info('Killing process')
        process.kill()
        output, _ = _read_async(process.stdout)
        stdout += output
        output, _ = _read_async(process.stderr)
        stderr += output
    process.wait()
    return stdout, stderr


def _clean_up(ctx, process, success, waiting_for_output, timeout_terminate):
    ctx.logger.info('Cleaning up')
    stdout, stderr = '', ''
    if success:
        process.wait()
    else:
        stdout, stderr = _manually_clean_up(
            ctx,
            process,
            waiting_for_output,
            timeout_terminate,
        )
    process.stdout.close()
    process.stderr.close()
    ctx.logger.info('Cleaned up')
    return stdout, stderr


def run_process(
        ctx,
        command,
        waiting_for_output,
        timeout_terminate
):
    ctx.logger.info('Starting process')
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for fd in process.stdout, process.stderr:
        _set_ononblock(fd)
    stdout, stderr, success = _read_fds(ctx, process, waiting_for_output)
    new_stdout, new_stderr = _clean_up(
        ctx,
        process,
        success,
        waiting_for_output,
        timeout_terminate
    )
    stdout += new_stdout
    stderr += new_stderr
    ctx.logger.info('Finishing process')
    return process.returncode, stdout, stderr
