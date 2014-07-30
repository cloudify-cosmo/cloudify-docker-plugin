from cloudify import exceptions

from docker_plugin import tasks
from docker_plugin import docker_wrapper

from TestCaseBase import TestCaseBase


_EMPTY_BUILD_OUTPUT = None
_EMPTY_IMPORT_OUTPUT = ''
_EMPTY_ID = ''
_NON_HASH_ID = 'z2318d26665ef'
_NON_ALPHANUM_ID = '2_318d26665ef'
_LONG_ID = 'ba5877dc9beca5a0af9521846e79419e98575a11cbfe1ff2ad2e95302cff26bff'
_SHORT_ID = '318d26665ef'
_VALID_ID = '2318d26665ef'
_IDS = [
    (_NON_HASH_ID, False),
    (_NON_ALPHANUM_ID, False),
    (_LONG_ID, False),
    (_SHORT_ID, False),
    (_VALID_ID, True)
]


class TestPrivateMethods(TestCaseBase):
    def build_image_get_id(self):
        self.assertRaises(
            exceptions.RecoverableError,
            docker_wrapper._get_build_image_id,
            self.ctx,
            self.client,
            _EMPTY_IMPORT_OUTPUT
        )

    def is_image_id_valid(self):
        [
            self.assertEqual(
                docker_wrapper._is_image_id_valid(self.ctx, img_id),
                is_valid
            )
            for (img_id, is_valid)
            in _IDS
        ]
