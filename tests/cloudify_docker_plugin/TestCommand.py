import time

from docker_plugin import tasks
from TestCaseBase import TestCaseBase


class TestCommand(TestCaseBase):
    def runTest(self):
        tasks.create(self.ctx)
        (containers, top_table, logs) = tasks.run(self.ctx)
        time.sleep(2)
        self.assertEqual(
            self.client.inspect_container(
                self.ctx.runtime_properties['container']
            )['State']['ExitCode'],
            0
        )
        self.assertTrue("Hello" in logs)
