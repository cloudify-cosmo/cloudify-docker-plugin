import os

from docker_plugin import tasks
from TestCaseBase import TestCaseBase


_DIR = '/tmp/test_folder' + '.' + str(os.getpid())
_FILE = 'test_file'
_FILE_PATH = _DIR + '/' + _FILE
_MNT_DIR = '/mnt'
_CONT_FILE_PATH = _MNT_DIR + '/' + _FILE
_TEXT = "Sample text\n" # The `\n' is **extremely** important.


class TestVolumes(TestCaseBase):

    def runTest(self):
        tasks.create(self.ctx)
        (containers, top_table, logs) = tasks.run(self.ctx)
        self.assertEqual(logs, _TEXT)

    def setUp(self):
        super(TestVolumes, self).setUp()
        self.ctx.properties['container_create'].update(
            {
                'volumes': [_MNT_DIR],
                'command': 'sh -c \'/bin/cat ' + _CONT_FILE_PATH + '; sleep 1\''
            }
        )
        self.ctx.properties['container_start'].update(
            {'binds': {_DIR: {'bind': _MNT_DIR}}}
        )
        os.mkdir(_DIR, 0755)
        with open(_FILE_PATH, 'w') as f:
            f.write(_TEXT)

    def tearDown(self):
        os.remove(_FILE_PATH)
        os.rmdir(_DIR)
        super(TestVolumes, self).tearDown()
