import unittest2 as unittest

from ..testing import FUNCTIONAL_TESTING


class TestCatalogPatch(unittest.TestCase):
    layer = FUNCTIONAL_TESTING

    def setUp(self):
        from zope.event import notify
        from zope.traversing.interfaces import BeforeTraverseEvent

        # Manually set up the browser layer, see:
        # https://dev.plone.org/ticket/11673
        notify(BeforeTraverseEvent(
            self.layer['portal'],
            self.layer['request']
        ))

    @property
    def catalog(self):
        return self.layer['portal'].portal_catalog

    def setLanguage(self, language_id):
        from Products.CMFPlone.interfaces import IPloneSiteRoot
        from Products.PloneLanguageTool.interfaces import INegotiateLanguage
        from collective.multilingual.interfaces import IBrowserLayer

        site = self.layer['portal']
        assert language_id != "en"

        class NegotiateLanguage(object):
            def __init__(self, site, request):
                self.default_language = "en"
                self.language = language_id
                self.language_list = ["en", language_id]

        site.getSiteManager().registerAdapter(
            NegotiateLanguage,
            (IPloneSiteRoot, IBrowserLayer),
            INegotiateLanguage
        )

        from Products.CMFCore.utils import getToolByName
        lt = getToolByName(site, 'portal_languages', None)

        if lt is not None:
            lt.setLanguageBindings()

        self.assertEqual(
            language_id,
            lt.getPreferredLanguage(),
        )

    def test_callable(self):
        result = self.catalog()
        languages = set(brain.language for brain in result)
        self.assertEqual(languages, set([""]))

    def test_all(self):
        result = self.catalog(language='all')
        languages = set(brain.language for brain in result)
        self.assertEqual(languages, set(["", "da", "de"]))

    def test_search_language(self):
        result = self.catalog(language="da")
        languages = set(brain.language for brain in result)
        self.assertTrue(result)
        self.assertEqual(languages, set(["da"]))

    def test_search_current_language(self):
        self.setLanguage("da")
        result = self.catalog()
        languages = set(brain.language for brain in result)
        self.assertTrue(result)
        self.assertEqual(languages, set(["da"]))

    def test_explicit_search_for_languageless(self):
        self.setLanguage("da")
        page = self.layer['portal']['da']['forside']
        page._p_activate()
        language = page.__dict__.pop('language', None)
        self.assertEqual(language, "da")
        page.reindexObject()
        result = self.catalog(language=None)
        languages = set(brain.language for brain in result)
        self.assertEqual(languages, set([None]))
        self.assertTrue(page in [brain.getObject() for brain in result])

    def test_default_search_finds_languageless(self):
        self.setLanguage("da")
        page = self.layer['portal']['da']['forside']
        page._p_activate()
        language = page.__dict__.pop('language', None)
        self.assertEqual(language, "da")
        page.reindexObject()
        result = self.catalog()
        languages = set(brain.language for brain in result)
        self.assertEqual(languages, set(["da", None]))
        self.assertTrue(page in [brain.getObject() for brain in result])

    def test_path_search_cancels_current_language(self):
        self.setLanguage("da")
        result = self.catalog(path={'query': '/plone/folder'})
        self.assertTrue(result)
        languages = set(brain.language for brain in result)
        self.assertEqual(languages, set([""]))
