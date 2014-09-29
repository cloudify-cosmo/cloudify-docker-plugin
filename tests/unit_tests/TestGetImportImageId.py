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


from cloudify import exceptions

from docker_plugin import docker_wrapper

from tests.TestWithMockupCtx import TestWithMockupCtx


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
            self.client,
            output
        )

    def test_empty_output(self):
        self._invalid_output('')

    def test_no_id(self):
        self._invalid_output(_NO_ID_OUTPUT)

    def test_no_quotes(self):
        self._invalid_output(_NO_QUOTES)

    def test_wrong_quotes(self):
        self._invalid_output(_WRONG_QUOTES)

    def test_valid_output(self):
        self.assertEqual(
            _IMAGE_ID,
            docker_wrapper._get_import_image_id(
                self.client,
                _VALID_OUTPUT
            )
        )
