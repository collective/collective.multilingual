from .i18n import MessageFactory as _
from .interfaces import IMultilingual
from .utils import logger
from Acquisition import aq_base
from plone.dexterity.interfaces import IDexterityContainer
from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import resolveDottedName
from Products.CMFCore.utils import getToolByName
from zope.component import getSiteManager
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
import six


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
class Translations(object):
    def __call__(self, context):
        terms = []
        catalog = getToolByName(context, "portal_catalog")
        display_languages = context.REQUEST.locale.displayNames.languages

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
                    u"${language}: ${title}",
                    mapping={
                        "language": display_languages.get(obj.language, _(u"Neutral")),
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
                    term = SimpleTerm(uuid, uuid, _(u"Missing"))

                terms.append(term)

        return DexterityContentVocabulary(createTerm, terms)


@implementer(IVocabularyFactory)
class FTIs(object):
    interface = IDexterityContent

    def __call__(self, context):
        sm = getSiteManager(context)
        ftis = sm.getAllUtilitiesRegisteredFor(IDexterityFTI)

        terms = []
        for fti in ftis:
            cls = resolveDottedName(fti.klass)
            if self.interface.implementedBy(cls):
                terms.append(SimpleTerm(fti, fti.id, fti.title))

        return SimpleVocabulary(terms)


class ContainerFTIs(FTIs):
    interface = IDexterityContainer


@implementer(IVocabularyFactory)
class Indexes(object):
    def __call__(self, context):
        try:
            catalog = context.portal_catalog
        except AttributeError as exc:
            logger.warn("%s: %r" % (exc, context))
            terms = []
        else:
            terms = [
                SimpleTerm(name, six.text_type(name), six.text_type(name))
                for name in sorted(catalog.indexes())
            ]

        return SimpleVocabulary(terms)
