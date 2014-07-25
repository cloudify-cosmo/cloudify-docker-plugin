import copy

from cloudify import exceptions

from docker_plugin import tasks
from TestCaseBase import TestCaseBase


class TestExceptions(TestCaseBase):
    def wrongPathToImage(self):
        p = copy.deepcopy(self.ctx.properties['image'])
        self.ctx.properties['image'].update({'path': "wrong path"})
        self.assertRaises(
            exceptions.NonRecoverableError,
            tasks.create,
            self.ctx
        )
        self.assertRaises(KeyError, tasks.run, self.ctx)

    def wrongCommand(self):
        self.ctx.properties['container_create'].update(
            {'command': "wrong command"}
        )
        tasks.create(self.ctx)
        self.assertRaises(exceptions.NonRecoverableError, tasks.run, self.ctx)

    def wrongVolumes(self):
        tasks.create(self.ctx)
        DIR = 'wrong_directory'
        MNT_DIR = 'wrong_mnt'
        self.ctx.properties['container_start'].update(
            {'binds': {DIR: {'bind': MNT_DIR}}}
        )
        self.assertRaises(exceptions.NonRecoverableError, tasks.run, self.ctx)
