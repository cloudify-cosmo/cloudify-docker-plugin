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

from tests.TestCaseBase import TestCaseBase


_SUCCESS_RES = 'OK'


class TestTryCalling(TestCaseBase):
    _was_exception = False

    def _raise_always_recoverable(self):
        raise exceptions.RecoverableError('Test always RecoverableError')

    def _raise_once_recoverable(self):
        if self._was_exception:
            return _SUCCESS_RES
        else:
            self._was_exception = True
            raise exceptions.RecoverableError('Test once RecoverableError')

    def _raise_nonrecoverable(self):
        raise exceptions.NonRecoverableError('Test NonRecoverableError')

    def test_raise_nonrecoverable(self):
        self.assertRaises(
            exceptions.NonRecoverableError,
            self._try_calling,
            self._raise_nonrecoverable
        )

    def test_raise_always_recoverable(self):
        self.assertRaises(
            exceptions.NonRecoverableError,
            self._try_calling,
            self._raise_always_recoverable
        )

    def test_raise_once_recoverable(self):
        self.assertEqual(
            _SUCCESS_RES,
            self._try_calling(self._raise_once_recoverable)
        )

    def test_raise_recoverable_with_limit(self):
        self.assertRaises(
            exceptions.NonRecoverableError,
            self._try_calling,
            self._raise_once_recoverable,
            max_retries_number=1
        )

    def test_no_exception(self):
        self.assertEqual(
            _SUCCESS_RES,
            self._try_calling(lambda: _SUCCESS_RES)
        )

    def tearDown(self):
        pass
