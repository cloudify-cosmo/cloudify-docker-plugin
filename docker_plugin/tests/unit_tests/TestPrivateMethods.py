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


from docker_plugin import docker_wrapper

from docker_plugin.tests.unit_tests.TestWithMockupCtx import TestWithMockupCtx


_EMPTY_ID = ''
_NON_HASH_ID = 'z2318d26665ef'
_NON_ALPHANUM_ID = '2_318d26665ef'
_LONG_ID = 'ba5877dc9beca5a0af9521846e79419e98575a11cbfe1ff2ad2e95302cff26bff'
_SHORT_ID = '318d26665ef'
_VALID_ID = '2318d26665ef'


class TestIsImageIdValid(TestWithMockupCtx):
    def _assert_image_id(self, image_id, is_valid):
        self.assertEqual(
            docker_wrapper._is_image_id_valid(image_id),
            is_valid
        )

    def test_valid_id(self):
        self._assert_image_id(_VALID_ID, True)

    def test_non_alphanum_id(self):
        self._assert_image_id(_NON_ALPHANUM_ID, False)

    def test_too_long_id(self):
        self._assert_image_id(_LONG_ID, False)

    def test_too_short_id(self):
        self._assert_image_id(_SHORT_ID, False)

    def test_empty_id(self):
        self._assert_image_id(_EMPTY_ID, False)

    def test_non_hash_id(self):
        self._assert_image_id(_NON_HASH_ID, False)
