import subprocess
import threading
import time
from fcntl import fcntl, F_GETFL, F_SETFL
from os import O_NONBLOCK
import os


_PROCCESS_COMMAND = './test_script.sh'
_MAX_WAITING_TIME = 3
_TIMEOUT = 3


def get_output(pipe, stream, msg):
    end_of_output, wait_output = False, False
    output = ''
    try:
        out = stream.read()
    except IOError:
        # TODO right error
        wait_output = True
        print "wait", msg
    else:
        if not out:
            print "end"
            end_of_output = True
        else:
            output = out
    finally:
        return end_of_output, wait_output, output


def read_streams(pipe):
    end_of_output, end_of_stdout, end_of_stderr = False, False, False
    time_no_output = 0
    stdout, stderr = '', ''
    hung_up = False
    while not end_of_output and not hung_up:
        if not end_of_stdout:
            end_of_stdout, wait_stdout, new_stdout = get_output(pipe, pipe.stdout, "stdout")
        stdout += new_stdout
        if not end_of_stderr:
            end_of_stderr, wait_stderr, new_stderr = get_output(pipe, pipe.stderr, "stderr")
        stderr += new_stderr
        end_of_output = end_of_stdout and end_of_stderr
        if (not end_of_output) and (end_of_stdout or wait_stdout) and (end_of_stderr or wait_stderr):
            if time_no_output >= _MAX_WAITING_TIME:
                print("Process {} hung up".format(_PROCCESS_COMMAND))
                hung_up = True
            else:
                time_no_output += 1
                time.sleep(1)
        else:
            time_no_output = 0
    return stdout, stderr, not hung_up

def _killer(list_is_running, lock, pipe):
    with lock:
        if list_is_running[0]:
            pipe.kill()
            print "pipe kill"

def run_proccess():
    pipe = subprocess.Popen(
        [_PROCCESS_COMMAND],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout_flags = fcntl(pipe.stdout, F_GETFL)
    fcntl(pipe.stdout, F_SETFL, stdout_flags | O_NONBLOCK)
    stderr_flags = fcntl(pipe.stderr, F_GETFL)
    fcntl(pipe.stderr, F_SETFL, stderr_flags | O_NONBLOCK)
    stdout, stderr, success = read_streams(pipe)
    # TODO what to close (pipe)
    if success:
        pipe.wait()
    else:
        pipe.terminate()
        print("kill 15")
        still_running = True
        lock = threading.Lock()
        t = threading.Timer(5, _killer, [[still_running], lock, pipe])
        t.start()
        pipe.wait()
        with lock:
            still_running = False
        t.cancel()
    pipe.stdout.close()
    pipe.stderr.close()
    if success and pipe.returncode == 0:
        print("success")
    else:
        #TODO error cloudify
        print("error")

    print pipe.returncode
    print("stdout:\n\n\n{}".format(stdout[-20:]))
    print("stderr:\n\n\n{}".format(stderr[-20:]))


if __name__ == '__main__':
    run_proccess()
