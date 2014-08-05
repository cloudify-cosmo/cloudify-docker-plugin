from cloudify import exceptions

from docker_plugin import docker_wrapper

from TestWithMockupCtx import TestWithMockupCtx


_BEGINNING = ('{"status":"Downloading from http://www.img.com/ubuntu.tar"}\n')

_END = ('{"status":"Importing","progressDetail":{"current":'
        '189006848,"total":189006848,"start":1406892052},"progress":'
        '"[==================================================\u003e]'
        '189 MB/189 MB"}')

_MIDDLE = ('{"status":"Importing","progressDetail":{"current":188274377,'
           '"total":189006848,"start":1406892052},"progress":'
           '"[=================================================\u003e ]'
           '188.3 MB/189 MB 0"}{"status":"Importing","progressDetail":'
           '{"current":188800001,"total":189006848,"start":1406892052},'
           '"progress":"[================================================='
           '\u003e ] 188.8 MB/189 MB 0"}')

_IMAGE_ID = 'fb38893eb079981728e06b98e5bb896684a1cc874cbdaefa129b43620b1501b1'

_VALID_OUTPUT = ('{}{}{{"status":"{}"}}\n{}'
                 .format(_BEGINNING, _MIDDLE, _IMAGE_ID, _END))

_WRONG_QUOTES = ('{}{}{{"status":""{}"}}\n{}'
                 .format(_BEGINNING, _MIDDLE, _IMAGE_ID, _END))


_NO_ID_OUTPUT = ('{}{}{{"status":""}}\n{}'
                 .format(_BEGINNING, _MIDDLE, _END))

_NO_QUOTES = _VALID_OUTPUT.replace('"', ' ')


class TestGetImportImageId(TestWithMockupCtx):
    def _invalid_output(self, output):
        self.assertRaises(
            exceptions.NonRecoverableError,
            docker_wrapper._get_import_image_id,
            self.ctx,
            self.client,
            output
        )

    def empty_output(self):
        self._invalid_output('')

    def no_id(self):
        self._invalid_output(_NO_ID_OUTPUT)

    def no_quotes(self):
        self._invalid_output(_NO_QUOTES)

    def wrong_quotes(self):
        self._invalid_output(_WRONG_QUOTES)

    def valid_output(self):
        self.assertEqual(
            _IMAGE_ID,
            docker_wrapper._get_import_image_id(
                self.ctx,
                self.client,
                _VALID_OUTPUT
            )
        )
