from .i18n import MessageFactory as _
from .interfaces import IMultilingual
from .utils import logger
from Acquisition import aq_base
from plone import api
from plone.dexterity.interfaces import IDexterityContainer
from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import resolveDottedName
from zope.component import getAllUtilitiesRegisteredFor
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class DexterityContentVocabulary(SimpleVocabulary):
    def __init__(self, createTerm, terms):
        SimpleVocabulary.__init__(self, terms)
        self.createTerm = createTerm

    def __contains__(self, value):
        try:
            self.getTerm(value)
        except LookupError:
            return False

        return True

    def getTerm(self, value):
        return self.getTermByToken(value)

    def getTermByToken(self, token):
        try:
            return SimpleVocabulary.getTermByToken(self, token)
        except LookupError:
            return self.createTerm(token)


@implementer(IVocabularyFactory)
class Translations:
    def __call__(self, context):
        terms = []
        portal = api.portal.get()
        request = portal.REQUEST
        catalog = api.portal.get_tool("portal_catalog")
        display_languages = request.locale.displayNames.languages

        def uuidToObject(uuid):
            if uuid:
                result = catalog(UID=uuid)

                if len(result) == 1:
                    return result[0].getObject()

            raise LookupError(uuid)

        def createTerm(uuid):
            obj = uuidToObject(uuid)
            return SimpleTerm(
                uuid,
                uuid,
                _(
                    "${language}: ${title}",
                    mapping={
                        "language": display_languages.get(obj.language, _("Neutral")),
                        "title": obj.title,
                    },
                ),
            )

        if IMultilingual.providedBy(context):
            for uuid in getattr(aq_base(context), "translations", ()) or ():
                try:
                    term = createTerm(uuid)
                except LookupError:
                    logger.warn("can't resolve reference: %r." % uuid)
                    term = SimpleTerm(uuid, uuid, _("Missing"))

                terms.append(term)

        return DexterityContentVocabulary(createTerm, terms)


@implementer(IVocabularyFactory)
class FTIs:
    interface = IDexterityContent

    def __call__(self, context):
        ftis = getAllUtilitiesRegisteredFor(IDexterityFTI)

        terms = []
        for fti in ftis:
            cls = resolveDottedName(fti.klass)
            if self.interface.implementedBy(cls):
                terms.append(SimpleTerm(fti, fti.id, fti.title))

        return SimpleVocabulary(terms)


class ContainerFTIs(FTIs):
    interface = IDexterityContainer


@implementer(IVocabularyFactory)
class Indexes:
    def __call__(self, context):
        catalog = api.portal.get_tool("portal_catalog")
        terms = [
            SimpleTerm(name, str(name), str(name)) for name in sorted(catalog.indexes())
        ]
        return SimpleVocabulary(terms)


IndexesFactory = Indexes()
