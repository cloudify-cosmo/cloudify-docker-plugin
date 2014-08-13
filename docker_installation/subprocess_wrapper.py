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
import logging
import os
import select
import subprocess
import time


logging.basicConfig(level=logging.INFO)


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


def _read_fds(process, timeout):
    logging.info('Waiting for subprocess to finish...')
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
            logging.error('Subprocess hung up')
            hung_up = True
            break
        for fd in read_fds:
            output, fds[fd.fileno()]['eof'] = _read_async(fd)
            fds[fd.fileno()]['output'] += output
        if all(fds[fd]['eof'] for fd in fds):
            logging.info('Subprocess finished')
            hung_up = False
            break
    return (
        fds[process.stdout.fileno()]['output'],
        fds[process.stderr.fileno()]['output'],
        not hung_up
    )


def _manually_clean_up(process, waiting_for_output, timeout_terminate):
    logging.info('Terminating process')
    process.terminate()
    # This behaviour can be changed in Python 3 due to incomplete
    # 'subprocess.Popen.wait' implementation in Python 2.7.
    time.sleep(timeout_terminate)
    process.kill()
    logging.info('Process terminated')
    stdout, _ = _read_async(process.stdout)
    stderr, _ = _read_async(process.stderr)
    process.wait()
    return stdout, stderr


def _clean_up(process, success, waiting_for_output, timeout_terminate):
    logging.info('Cleaning up')
    stdout, stderr = '', ''
    if success:
        process.wait()
    else:
        stdout, stderr = _manually_clean_up(
            process,
            waiting_for_output,
            timeout_terminate,
        )
    process.stdout.close()
    process.stderr.close()
    logging.info('Cleaned up')
    return stdout, stderr


def run_process(
        command,
        waiting_for_output,
        timeout_terminate
):
    logging.info('Starting process')
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for fd in process.stdout, process.stderr:
        _set_ononblock(fd)
    stdout, stderr, success = _read_fds(process, waiting_for_output)
    new_stdout, new_stderr = _clean_up(
        process,
        success,
        waiting_for_output,
        timeout_terminate
    )
    stdout += new_stdout
    stderr += new_stderr
    logging.info('Finishing process')
    return process.returncode, stdout, stderr
