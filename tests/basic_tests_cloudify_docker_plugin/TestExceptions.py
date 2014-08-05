from cloudify import exceptions

from docker_plugin import tasks
from tests.TestCaseBase import TestCaseBase


_WRONG_PATH = 'wrong path'
_WRONG_CMD = 'wrong command'
_DIR = 'wrong_directory'
_MNT_DIR = 'wrong_mnt'


class TestExceptions(TestCaseBase):
    def test_wrong_path_to_image(self):
        self.ctx.properties['image_build'].update({'path': _WRONG_PATH})
        self.assertRaises(
            exceptions.NonRecoverableError,
            tasks.create,
            self.ctx
        )
        self.assertRaises(exceptions.NonRecoverableError, tasks.run, self.ctx)

    def test_wrong_command(self):
        self.ctx.properties['container_create'].update({'command': _WRONG_CMD})
        tasks.create(self.ctx)
        self.assertRaises(exceptions.NonRecoverableError, tasks.run, self.ctx)

    def test_wrong_volumes(self):
        tasks.create(self.ctx)
        self.ctx.properties['container_start'].update(
            {'binds': {_DIR: {'bind': _MNT_DIR}}}
        )
        self.assertRaises(exceptions.NonRecoverableError, tasks.run, self.ctx)

    def test_no_image_path(self):
        image = self.ctx.properties.pop('image_build')
        image = self.ctx.properties.pop('image_import')
        self.assertRaises(
            exceptions.NonRecoverableError,
            tasks.create,
            self.ctx
        )
