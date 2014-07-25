from docker_plugin import tasks
from TestCaseBase import TestCaseBase


class TestStopAndRun(TestCaseBase):
    def runTest(self):
        tasks.create(self.ctx)
        (containers, top_table, logs) = tasks.run(self.ctx)
        self.assertGreater(len(containers), 0)
        self.assertTrue(
            self.client.inspect_container(
                self.ctx.runtime_properties['container']
            )['State']['Running']
        )
        tasks.stop(self.ctx)
        self.assertFalse(
            self.client.inspect_container(
                self.ctx.runtime_properties['container']
            )['State']['Running']
        )
        tasks.run(self.ctx)
        self.assertTrue(
            self.client.inspect_container(
                self.ctx.runtime_properties['container']
            )['State']['Running']
        )
