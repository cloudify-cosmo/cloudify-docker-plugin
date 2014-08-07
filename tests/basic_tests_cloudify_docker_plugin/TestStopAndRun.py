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


from docker_plugin import tasks
from tests.TestCaseBase import TestCaseBase


class TestStopAndRun(TestCaseBase):
    def test_stop_and_run(self):
        self._try_calling(tasks.create, [self.ctx])
        self._try_calling(tasks.run, [self.ctx])
        self._assert_container_running(self.assertTrue)
        self._try_calling(tasks.stop, [self.ctx])
        self._assert_container_running(self.assertFalse)
        self._try_calling(tasks.run, [self.ctx])
        self._assert_container_running(self.assertTrue)
