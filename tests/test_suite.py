import unittest

from cloudify_docker_plugin.TestStopAndRun import TestStopAndRun
from cloudify_docker_plugin.TestCommand import TestCommand
from cloudify_docker_plugin.TestPortsConfig import TestPortsConfig
from cloudify_docker_plugin.TestVolumes import TestVolumes
from cloudify_docker_plugin.TestExceptions import TestExceptions
from cloudify_docker_plugin.TestPrivateMethods import TestPrivateMethods


class DockerSuite(unittest.TestSuite):

    def __init__(self):
        super(DockerSuite, self).__init__()
        self.addTest(TestStopAndRun())
        self.addTest(TestCommand('command_success'))
        self.addTest(TestCommand('command_failure'))
        self.addTest(TestPortsConfig())
        self.addTest(TestVolumes())
        self.addTest(TestExceptions('wrongPathToImage'))
        self.addTest(TestExceptions('wrongCommand'))
        self.addTest(TestExceptions('wrongVolumes'))
        self.addTest(TestExceptions('noImagePath'))
        self.addTest(TestPrivateMethods('build_image_get_id'))
        self.addTest(TestPrivateMethods('is_image_id_valid'))
