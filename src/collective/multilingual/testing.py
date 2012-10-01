from plone.app.testing import PloneSandboxLayer
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting


def dotted_name(interface):
    return "%s.%s" % (interface.__module__, interface.__name__)


class Fixture(PloneSandboxLayer):
    defaultBases = (PLONE_FIXTURE, )

    def setUpZope(self, app, configurationContext):
        import collective.multilingual
        self.loadZCML(package=collective.multilingual)

    def setUpPloneSite(self, portal):
        self.applyProfile(portal, 'collective.multilingual:default')

        # Make test user a content contributor.
        from plone.app.testing import TEST_USER_ID
        from plone.app.testing import setRoles
        setRoles(portal, TEST_USER_ID, ['Member', 'Contributor'])

        self.setUpContentTypes(portal)
        self.setUpLanguages(portal)
        self.setUpContent(portal)

    def setUpContent(self, portal):
        from plone.dexterity.utils import createContentInContainer
        from plone.uuid.interfaces import IUUID

        # 1. Create front page:
        page = createContentInContainer(
            portal, "Item", id="front-page", title=u"Front page"
            )

        # 2. Create language folders /da and /de:
        danish = createContentInContainer(
            portal, "Container", id="da", language=u"da",
            )

        createContentInContainer(
            portal, "Container", id="de", language=u"de",
            )

        # 3. Create a Danish translation of the front page:
        createContentInContainer(
            danish, "Item", id="forside", title=u"Forside",
            language=u"da", translations=[str(IUUID(page))],
            )

        # 4. Create a folder in neutral language and a translation in
        #    Danish.
        folder1 = createContentInContainer(
            portal, "Container", id="folder",
            )

        # Note that there's something potentially confusing here (and
        # in (3) above): the ``translations`` relationship is actually
        # inverted in the object added event handler.
        createContentInContainer(
            portal, "Container", id="mappe",
            language=u"da", translations=[str(IUUID(folder1))]
            )

        # 5. Create a nested item (untranslated).
        createContentInContainer(
            folder1, "Item", id="item",
            )

    def setUpLanguages(self, portal):
        # Add "Danish" and "German" as supported languages.
        portal.portal_languages.addSupportedLanguage('da')
        portal.portal_languages.addSupportedLanguage('de')
        portal.portal_languages.addSupportedLanguage('es')

    def setUpContentTypes(self, portal):
        from plone.dexterity.fti import DexterityFTI
        from plone.dexterity.fti import register
        from plone.app.content.interfaces import INameFromTitle

        from collective.multilingual.interfaces import IMultilingual

        content_types = [
            ("Item", "plone.dexterity.content.Item", ()),
            ("Container", "plone.dexterity.content.Container", ("Item", )),
            ]

        # Set up Dexterity-based content types.
        for portal_type, klass, allowed_content_types in content_types:
            fti = DexterityFTI(portal_type)
            fti.allowed_content_types = allowed_content_types
            fti.behaviors = (
                dotted_name(IMultilingual),
                dotted_name(INameFromTitle),
                )
            fti.klass = klass
            register(fti)

            # There's got to be a better way :-)
            portal.portal_types._setOb(portal_type, fti)


FIXTURE = Fixture()

INTEGRATION_TESTING = IntegrationTesting(
    bases=(FIXTURE,),
    name="MultilingualFixture:Integration")
