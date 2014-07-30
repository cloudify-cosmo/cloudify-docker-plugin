from cloudify import exceptions

from docker_plugin import tasks
from TestCaseBase import TestCaseBase


_WRONG_PATH = 'wrong path'
_WRONG_CMD = 'wrong command'
_DIR = 'wrong_directory'
_MNT_DIR = 'wrong_mnt'


class TestExceptions(TestCaseBase):
    def wrongPathToImage(self):
        self.ctx.properties['image'].update({'path': _WRONG_PATH})
        self.assertRaises(
            exceptions.NonRecoverableError,
            tasks.create,
            self.ctx
        )
        self.assertRaises(KeyError, tasks.run, self.ctx)

    def wrongCommand(self):
        self.ctx.properties['container_create'].update({'command': _WRONG_CMD})
        tasks.create(self.ctx)
        self.assertRaises(exceptions.NonRecoverableError, tasks.run, self.ctx)

    def wrongVolumes(self):
        tasks.create(self.ctx)
        self.ctx.properties['container_start'].update(
            {'binds': {_DIR: {'bind': _MNT_DIR}}}
        )
        self.assertRaises(exceptions.NonRecoverableError, tasks.run, self.ctx)

    def noImagePath(self):
        image = self.ctx.properties.pop('image')
        self.assertRaises(
            exceptions.NonRecoverableError,
            tasks.create,
            self.ctx
        )
