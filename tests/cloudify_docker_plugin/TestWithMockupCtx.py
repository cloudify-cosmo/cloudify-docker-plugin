import unittest

import docker

from cloudify import mocks


class TestWithMockupCtx(unittest.TestCase):

    ctx = None
    client = None

    def setUp(self):
        self.client = docker.Client()
        self.ctx = mocks.MockCloudifyContext(properties={})
        # TODO(Zosia) temporary debug help
        self.ctx.logger.info('\n'+str(self.id)+'\n')
