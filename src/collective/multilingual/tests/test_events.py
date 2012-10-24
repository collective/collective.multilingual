import unittest2 as unittest

from ..testing import FUNCTIONAL_TESTING


class TestEvents(unittest.TestCase):
    layer = FUNCTIONAL_TESTING

    def test_inherit_language(self):
        page = self.layer['portal']['da']['forside']
        self.assertEqual(page.language, u"da")

    def test_copy_into_language_folder(self):
        folder = self.layer['portal']['folder']
        paste = folder.manage_copyObjects(['item'])
        target = self.layer['portal']['da']['mappe']
        result = target.manage_pasteObjects(paste)
        self.assertEqual(len(result), 1)
        new_id = result[0]['new_id']
        new_obj = target[new_id]
        from collective.multilingual.interfaces import ITranslationGraph
        graph = ITranslationGraph(new_obj)
        items = graph.getTranslations()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][0], '')
        self.assertEqual(items[0][1].getPhysicalPath(),
                         ('', 'plone', 'folder', 'item'))
        new_obj.aq_parent.setDefaultPage(new_id)

    def test_copy_into_same_folder(self):
        folder = self.layer['portal']['folder']
        paste = folder.manage_copyObjects(['item'])
        target = folder
        result = target.manage_pasteObjects(paste)
        self.assertEqual(len(result), 1)
        new_id = result[0]['new_id']
        new_obj = target[new_id]
        from collective.multilingual.interfaces import ITranslationGraph
        graph = ITranslationGraph(new_obj)
        items = graph.getTranslations()
        self.assertEqual(len(items), 0)
