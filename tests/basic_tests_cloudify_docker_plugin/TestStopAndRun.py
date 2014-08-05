from docker_plugin import tasks
from tests.TestCaseBase import TestCaseBase


class TestStopAndRun(TestCaseBase):
    def test_stop_and_run(self):
        tasks.create(self.ctx)
        tasks.run(self.ctx)
        self._assert_container_running(self.assertTrue)
        tasks.stop(self.ctx)
        self._assert_container_running(self.assertFalse)
        tasks.run(self.ctx)
        self._assert_container_running(self.assertTrue)
