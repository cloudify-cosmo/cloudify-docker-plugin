import unittest

from cloudify_docker_plugin.TestStopAndRun import TestStopAndRun
from cloudify_docker_plugin.TestCommand import TestCommand
from cloudify_docker_plugin.TestPortsConfig import TestPortsConfig
from cloudify_docker_plugin.TestVolumes import TestVolumes
from cloudify_docker_plugin.TestExceptions import TestExceptions
from cloudify_docker_plugin.TestPrivateMethods import TestPrivateMethods
from cloudify_docker_plugin.TestGetBuildImageId import TestGetBuildImageId
from cloudify_docker_plugin.TestGetImportImageId import TestGetImportImageId
from cloudify_docker_plugin.TestSubprocessWrapper import TestSubprocessWrapper
from cloudify_docker_plugin.TestNetwork import TestNetwork


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
        self.addTest(TestGetBuildImageId('empty_stream'))
        self.addTest(TestGetBuildImageId('valid_stream'))
        self.addTest(TestGetBuildImageId('invalid_stream'))
        self.addTest(TestPrivateMethods('is_image_id_valid'))
        self.addTest(TestGetImportImageId('valid_output'))
        self.addTest(TestGetImportImageId('empty_output'))
        self.addTest(TestGetImportImageId('no_id'))
        self.addTest(TestGetImportImageId('no_quotes'))
        self.addTest(TestGetImportImageId('wrong_quotes'))
        self.addTest(TestSubprocessWrapper('run_valid_process'))
        self.addTest(TestSubprocessWrapper('run_hung_up_process'))
        self.addTest(TestSubprocessWrapper('run_hung_up_on_terminate'))
        self.addTest(TestNetwork())
