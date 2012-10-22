import unittest2 as unittest

from ..testing import FUNCTIONAL_TESTING


class TestUtility(unittest.TestCase):
    layer = FUNCTIONAL_TESTING

    @property
    def testing(self):
        from plone.app import testing
        return testing

    def get_browser(self, login=True):
        from plone.testing.z2 import Browser
        browser = Browser(self.layer['app'])
        browser.handleErrors = False

        if login:
            browser.addHeader(
                'Authorization', 'Basic %s:%s' % (
                    self.testing.SITE_OWNER_NAME,
                    self.testing.SITE_OWNER_PASSWORD
                    ))

        return browser

    def test_edit_language_independent(self):
        browser = self.get_browser()
        page = self.layer['portal']['front-page']
        browser.open(page.absolute_url() + '/edit')
        form = browser.getForm(id="form")

        from collective.multilingual.interfaces import getLanguageIndependent
        from zope.i18n import translate

        language_independent = getLanguageIndependent(page)

        for field in language_independent:
            label = translate(field.title)
            control = form.getControl(label)
            control.value = 'foo'

        form.submit('Save')

        for obj in (page, self.layer['portal']['da']['forside']):
            for field in language_independent:
                value = getattr(obj, field.__name__)
                self.assertTrue('foo' in repr(value), value)

    def test_page_in_neutral_language(self):
        browser = self.get_browser()
        page = self.layer['portal']['front-page']
        browser.open(page.absolute_url())
        self.assertTrue(
            browser.getLink(id='translate_into_da').url.endswith('/forside'),
            )
        self.assertTrue(
            '++add++Item' in \
            browser.getLink(id='translate_into_de').url
            )
        self.assertTrue(
            'setup-language' in \
            browser.getLink(id='translate_into_es').url
            )

    def test_nested_page_in_neutral_language_into_danish(self):
        browser = self.get_browser()
        page = self.layer['portal']['folder']['item']
        browser.open(page.absolute_url())
        browser.getLink(id='translate_into_da').click()
        self.assertFalse(
            'id="multilingual-parent-not-translated-notice"' \
            in browser.contents
            )

    def test_nested_page_in_neutral_language_into_german(self):
        browser = self.get_browser()
        page = self.layer['portal']['folder']['item']
        browser.open(page.absolute_url())
        browser.getLink(id='translate_into_de').click()
        self.assertTrue(
            'id="multilingual-parent-not-translated-notice"' \
            in browser.contents
            )

    def test_page_in_other_language(self):
        browser = self.get_browser()
        page = self.layer['portal']['da']['forside']
        browser.open(page.absolute_url())

    def test_settings(self):
        browser = self.get_browser()
        page = self.layer['portal']
        browser.open(page.absolute_url() + "/@@multilingual-settings")

        import lxml.html
        root = lxml.html.fromstring(browser.contents)
        table = root.get_element_by_id('multilingual-statistics')
        tds = [td.text_content().strip() for td in table.iterdescendants('td')]
        self.assertEqual(
            tds,
            ['Any', '8', '100%',
             'Danish', '3', '38%',
             'English', '0', '0%',
             'German', '1', '12%',
             'Spanish', '0', '0%']
            )

    def test_setup_language(self):
        browser = self.get_browser()
        page = self.layer['portal']
        browser.open(page.absolute_url() + "/@@setup-language?language=de")

    def test_setup_language_folder_and_add_translation(self):
        browser = self.get_browser()
        page = self.layer['portal']['front-page']
        browser.open(page.absolute_url())
        link = browser.getLink(id='translate_into_es')
        link.click()
        self.assertTrue('Create language folder' in browser.contents)
        form = browser.getForm(id="form")

        # Test form defaults:
        equals = lambda name, text: self.assertEqual(form.getControl(
            name).value, text)

        equals('Title', 'Spanish')
        equals('Description', 'This folder contains content in Spanish.')
        equals('Content type', ['Container'])

        # Submit form.
        form.submit('Create')
        self.assertTrue('Container created.' in browser.contents)
        self.assertTrue('es' in self.layer['portal'].objectIds())

        # It's a site root.
        from plone.app.layout.navigation.interfaces import INavigationRoot
        self.assertTrue(
            INavigationRoot.providedBy(self.layer['portal']['es'])
        )

        # We've been redirected to the add form:
        self.assertTrue(
            'http://nohost/plone/es/++add++Item' in
            browser.url
            )

        # Let's add the content.
        form = browser.getForm(id='form')
        form.getControl('Title').value = 'Portada'
        form.submit('Save')

        # Assert that the page has been created.
        self.assertTrue('portada' in self.layer['portal']['es'])
