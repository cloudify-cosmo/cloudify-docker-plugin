import os
import time

from docker_plugin import tasks
from TestCaseBase import TestCaseBase


# Still under development
class TestUsingImage(TestCaseBase):
    def runTest(self):
        # TODO Change image to smaller one
        # TODO Change the command
        cmd = 'nc -nvl 8080 < tests/cloudify_docker_plugin/command &'
        os.system(cmd)
        time.sleep(1)
        image = "http://localhost:8080"
        self.ctx.properties['image_import'].update(
            {'src': image}
        )
        self.ctx.properties['container_remove'].update(
            {'remove_image': True}
        )
        tasks.create(self.ctx)
        (containers, top_table, logs) = tasks.run(self.ctx)
        self.assertTrue(
            self.client.inspect_container(
                self.ctx.runtime_properties['container']
            )['State']['Running']
        )
