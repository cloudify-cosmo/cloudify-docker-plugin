from docker_plugin import tasks
import TestWithMockupCtx


class TestImagePull(TestWithMockupCtx.TestWithMockupCtx):

    def test_pull(self):
        tasks.pull(image_pull={'repository': 'uric/nodecellar'})
