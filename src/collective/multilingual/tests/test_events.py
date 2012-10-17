import unittest2 as unittest

from ..testing import INTEGRATION_TESTING


class TestEvents(unittest.TestCase):
    layer = INTEGRATION_TESTING

    def test_inherit_language(self):
        page = self.layer['portal']['da']['forside']
        self.assertEqual(page.language, u"da")
