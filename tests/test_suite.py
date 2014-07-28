import unittest

from cloudify_docker_plugin.TestStopAndRun import TestStopAndRun
from cloudify_docker_plugin.TestCommand import TestCommand
from cloudify_docker_plugin.TestPortsConfig import TestPortsConfig
from cloudify_docker_plugin.TestVolumes import TestVolumes
from cloudify_docker_plugin.TestExceptions import TestExceptions


class DockerSuite(unittest.TestSuite):

    def __init__(self):
        super(DockerSuite, self).__init__()
        # self.addTest(TestStopAndRun())
        # self.addTest(TestCommand())
        # self.addTest(TestPortsConfig())
        # self.addTest(TestVolumes())
        # self.addTest(TestExceptions('wrongPathToImage'))
        self.addTest(TestExceptions('wrongCommand'))
        # self.addTest(TestExceptions('wrongVolumes'))
        self.addTest(TestExceptions('noImagePath'))
