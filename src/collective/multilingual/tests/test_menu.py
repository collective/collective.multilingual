import unittest2 as unittest

from ..testing import INTEGRATION_TESTING


def extract_langs(titles):
    """Extract the language identifier from an action menu title.

    The reason is that sometimes there will be additional text in the
    title, e.g. to inform a user that the language folder has not yet
    been set up.
    """

    langs = [title.split(' ', 1)[0] for title in titles]
    return set(lang for lang in langs if len(lang) <= 3)


def extract_actions(items):
    return dict(
        (item['extra']['id'], item['action']) for item in items
    )


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

    def test_default_page_in_folder_with_translation(self):
        page = self.layer['portal']['folder']['default-item']
        items = self.make_items(page)
        actions = extract_actions(items)
        self.assertTrue(
            '/mappe/++add++Item' in actions['translate_into_da']
        )
        from plone.uuid.interfaces import IUUID
        self.assertTrue(
            IUUID(page) in actions['translate_into_da']
        )

    def test_default_page_in_folder_without_translation(self):
        folder = self.layer['portal']['folder']
        folder.translations.clear()
        items = self.make_items(folder['default-item'])
        actions = extract_actions(items)
        self.assertTrue(
            '/da/++add++Container' in actions['translate_into_da']
        )
        from plone.uuid.interfaces import IUUID
        self.assertTrue(
            IUUID(folder) in actions['translate_into_da']
        )

    def test_translation_as_default_page_in_folder_with_translation(self):
        page = self.layer['portal']['da']['forside']
        items = self.make_items(page)
        actions = extract_actions(items)
        self.assertTrue('translate_into_da' not in actions)
        self.assertTrue(
            '/plone/front-page' in actions['translate_into_en']
        )
        self.assertTrue(
            '/plone/de/++add++Item' in actions['translate_into_de']
        )
        from plone.uuid.interfaces import IUUID
        self.assertTrue(
            IUUID(page) in actions['translate_into_de']
        )
