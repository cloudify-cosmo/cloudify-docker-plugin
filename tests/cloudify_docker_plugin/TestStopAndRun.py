from docker_plugin import tasks
from TestCaseBase import TestCaseBase


class TestStopAndRun(TestCaseBase):
    def runTest(self):
        tasks.create(self.ctx)
        tasks.run(self.ctx)
        self._assert_container_running(self.assertTrue)
        tasks.stop(self.ctx)
        self._assert_container_running(self.assertFalse)
        tasks.run(self.ctx)
        self._assert_container_running(self.assertTrue)
