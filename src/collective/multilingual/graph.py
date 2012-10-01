from plone.uuid.interfaces import IUUID
from zope.interface import implements
from zope.component import adapts
from zope.lifecycleevent import modified

from Products.CMFCore.utils import getToolByName
from Acquisition import aq_base

from .interfaces import IMultilingual
from .interfaces import ITranslationGraph
from .utils import logger


def _recurse(catalog, uuids):
    uuids = list(uuids)
    brains = catalog(UID=uuids)

    uuids = set()
    for brain in brains:
        yield brain

        try:
            translations = brain.translations
        except AttributeError:
            logger.warn("brain missing a translations attribute.")
            continue

        try:
            uuids |= set(translations)
        except TypeError:
            continue

    if not uuids:
        return

    for brain in _recurse(catalog, uuids):
        yield brain


class MultilingualTranslationGraph(object):
    implements(ITranslationGraph)
    adapts(IMultilingual)

    def __init__(self, context):
        self.context = context
        self.catalog = getToolByName(context, 'portal_catalog')
        self.uuid = str(IUUID(context))

    def getCanonicalContent(self, catalog=None):
        obj = self.getParent()
        if obj is None:
            return self.context

        if obj is self.context:
            logger.warn("integrity error; translation cycle.")
            return

        if not IMultilingual.providedBy(obj):
            logger.warn("integrity error; parent not translation-aware.")

        return ITranslationGraph(obj).getCanonicalContent()

    def getParent(self):
        result = self.catalog(translations=self.uuid)

        if len(result) == 0:
            return

        if len(result) > 1:
            logger.warn("integrity error; ambiguous relationship.")

        return result[0].getObject()

    def getTranslations(self):
        return list(self.iterTranslations())

    def iterTranslations(self):
        canonical = self.getCanonicalContent()
        if canonical is None:
            return

        objects = []

        # 1. Include canonical item only if different from context.
        if canonical is not self.context:
            objects.append(canonical)

        # 2. Start recursion with the canonical item's direct translations.
        uuids = getattr(aq_base(canonical), "translations", ())
        if uuids:
            uuids = set(uuids)

            # 3. Don't include the context of the graph.
            uuids.discard(self.uuid)

            for brain in _recurse(self.catalog, list(uuids)):
                obj = brain.getObject()

                # 4. We might appear again here due to recursion.
                if obj is self.context:
                    continue

                objects.append(obj)

        # 5. Now pair results with the language identifier.
        for obj in objects:
            lang_id = getattr(aq_base(obj), "language", None)
            if lang_id is None:
                logger.warning(
                    "expected language set on object: %s." %
                    "/".join(obj.getPhysicalPath())
                    )
            else:
                yield lang_id, obj

    def registerTranslation(self, parent):
        translations = set(getattr(aq_base(parent), "translations", ()))
        translations.add(self.uuid)
        parent.translations = translations
        modified(parent)

    def removeTranslation(self):
        result = self.catalog(translations=self.uuid)
        if len(result) != 1:
            raise ValueError("Translation parent not found.")

        obj = result[0].getObject()
        obj.translations = obj.translations - set(self.uuids)
        modified(obj)
