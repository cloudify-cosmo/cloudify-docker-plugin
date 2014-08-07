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


_BUILD_ID = 'ba5877dc9bec'
_EMPTY_STREAM_LIST = []
_VALID_STREAM_LIST = [
    '{{"stream":" ---\u003e {}\\n"}}\n'.format(_BUILD_ID),
    '{{"stream":"Successfully built {}\\n"}}\n'.format(_BUILD_ID)
]
_INVALID_STREAM_LIST = [
    '{{"stream":"Successfully built {}\\n"}}\n'.format(_BUILD_ID),
    '{{"stream":" ---\u003e {}\\n"}}\n'.format(_BUILD_ID)
]


class TestGetBuildImageId(TestWithMockupCtx):
    def _gen_stream(self, stream_list):
        for s in stream_list:
            yield s

    def test_empty_stream(self):
        self.assertRaises(
            exceptions.RecoverableError,
            docker_wrapper._get_build_image_id,
            self.ctx,
            self.client,
            self._gen_stream(_EMPTY_STREAM_LIST)
        )

    def test_valid_stream(self):
        self.assertEqual(
            _BUILD_ID,
            docker_wrapper._get_build_image_id(
                self.ctx,
                self.client,
                self._gen_stream(_VALID_STREAM_LIST)
            )
        )

    def test_invalid_stream(self):
        self.assertRaises(
            exceptions.NonRecoverableError,
            docker_wrapper._get_build_image_id,
            self.ctx,
            self.client,
            self._gen_stream(_INVALID_STREAM_LIST)
        )
