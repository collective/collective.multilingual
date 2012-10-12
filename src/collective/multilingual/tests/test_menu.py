import unittest

from ..testing import INTEGRATION_TESTING


def extract_langs(titles):
    """Extract the language identifier from an action menu title.

    The reason is that sometimes there will be additional text in the
    title, e.g. to inform a user that the language folder has not yet
    been set up.
    """

    return set([title.split(' ', 1)[0] for title in titles])


class TestMenu(unittest.TestCase):
    layer = INTEGRATION_TESTING

    def make_one(self, context):
        from collective.multilingual.browser.menu import TranslateMenu
        return TranslateMenu(context, self.layer['request'])

    def make_items(self, context):
        menu = self.make_one(context)
        return menu.getMenuItems(context, self.layer['request'])

    def test_portal(self):
        items = self.make_items(self.layer['portal'])
        self.assertEqual(items, [])

    def test_page_in_neutral_language(self):
        items = self.make_items(self.layer['portal']['front-page'])
        titles = set(item['title'] for item in items)
        self.assertEqual(extract_langs(titles), set(("de", "da", "es")))

    def test_page_in_other_language(self):
        items = self.make_items(self.layer['portal']['da']['forside'])
        titles = set(item['title'] for item in items)
        self.assertEqual(extract_langs(titles), set(("de", "en", "es")))
