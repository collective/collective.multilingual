import unittest

from ..testing import INTEGRATION_TESTING


class TestUtility(unittest.TestCase):
    layer = INTEGRATION_TESTING

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

    def test_page_in_neutral_language(self):
        browser = self.get_browser()
        page = self.layer['portal']['front-page']
        browser.open(page.absolute_url())
        self.assertTrue(
            'edit' in \
            browser.getLink(id='translate_into_da').url
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
