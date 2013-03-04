import functools

from zope.interface import implements
from zope.component import adapts

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Acquisition import aq_base

from plone.uuid.interfaces import IUUID
from plone.memoize.ram import store_in_cache

from .interfaces import IMultilingual
from .interfaces import ITranslationGraph
from .utils import logger
from .utils import getPersistentTranslationCounter

marker = object()


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


def cache(func):
    adapter = store_in_cache(func)

    @functools.wraps(func)
    def decorator(self, *args, **kwargs):
        counter = getPersistentTranslationCounter(self.context)
        key = "%s:%d" % (self.uuid, counter.value)
        cache = CacheProxy(adapter, key)
        return func(self, cache, *args, **kwargs)

    return decorator


class CacheProxy(object):
    __slots__ = "adapter", "key"

    def __init__(self, adapter, key):
        self.adapter = adapter
        self.key = key

    def get(self, default):
        try:
            return self.adapter[self.key]
        except KeyError:
            return default

    def set(self, result, value):
        self.adapter[self.key] = value
        return result


class MultilingualTranslationGraph(object):
    implements(ITranslationGraph)
    adapts(IMultilingual)

    def __init__(self, context):
        self.context = context
        self.catalog = getToolByName(context, 'portal_catalog')
        self.uuid = str(IUUID(context))

    def resolve(self, uuid):
        if uuid is not None:
            results = self.catalog(UID=uuid)
            if len(results) > 0:
                return results[0].getObject()
        return None

    @cache
    def getCanonicalContent(self, cache):
        uuid = cache.get(marker)
        if uuid is not marker:
            return self.resolve(uuid)

        obj = self.getParent()
        if obj is None:
            return cache.set(self.context, self.uuid)

        if obj is self.context:
            logger.warn("integrity error; translation cycle.")
            return

        if not IMultilingual.providedBy(obj):
            logger.warn("integrity error; parent not translation-aware.")

        try:
            obj = ITranslationGraph(obj).getCanonicalContent()
        except TypeError:
            logger.warn("Object does not have a translation graph.")
        else:
            return cache.set(obj, str(IUUID(obj)))

    @cache
    def getParent(self, cache):
        uuid = cache.get(marker)
        if uuid is not marker:
            return self.resolve(uuid)

        result = self.catalog(translations=self.uuid)

        if len(result) == 0:
            return cache.set(None, None)

        if len(result) > 1:
            logger.warn("integrity error; ambiguous relationship.")

        obj = result[0].getObject()
        return cache.set(obj, str(IUUID(obj)))

    @cache
    def getNearestTranslations(self, cache):
        value = cache.get(marker)
        if value is not marker:
            return [
                (lang_id, self.resolve(uuid), distance)
                for (lang_id, uuid, distance) in value
            ]

        lt = getToolByName(self.context, 'portal_languages')
        supported = lt.listSupportedLanguages()
        assert len(supported) > 1

        lang_items = []
        langs = set(lang[0] for lang in supported)
        default_lang = lt.getDefaultLanguage()
        distance = 0

        # 1. Objects appearing in the present translation graph.
        for lang_id, item in self.getTranslations():
            if not lang_id:
                lang_id = default_lang

            try:
                langs.remove(lang_id)
            except KeyError:
                # Appearently, this language is no longer
                # supported. Ignore it!
                continue

            entry = lang_id, item, distance
            lang_items.append(entry)

        # 2. Iterate through parent chain
        folder = self.context
        while langs and not IPloneSiteRoot.providedBy(folder):
            folder = folder.__parent__
            distance += 1
            if IMultilingual.providedBy(folder):
                translations = ITranslationGraph(folder).getTranslations()

                for lang_id, item in translations:
                    if not lang_id:
                        lang_id = default_lang
                    try:
                        langs.remove(lang_id)
                    except KeyError:
                        continue

                    lang_items.append((lang_id, item, distance))

        # 3. Process remaining supported languages.
        for lang_id in langs:
            lang_items.append((lang_id, None, -1))

        return cache.set(lang_items, [
            (lang_id, str(IUUID(item)) if item is not None else None, distance)
            for (lang_id, item, distance) in lang_items])

    @cache
    def getTranslations(self, cache):
        value = cache.get(marker)
        if value is not marker:
            return [
                (lang_id, self.resolve(uuid))
                for (lang_id, uuid) in value
            ]

        result = list(self.iterTranslations())
        return cache.set(result, [
            (lang_id, str(IUUID(obj)))
            for (lang_id, obj) in result])

    def iterTranslations(self):
        canonical = self.getCanonicalContent()
        if canonical is None:
            return

        objects = []

        # 1. Include canonical item only if different from context.
        if canonical is not self.context:
            objects.append(canonical)

        # 2. Start recursion with the canonical item's direct translations.
        uuids = getattr(aq_base(canonical), "translations", ()) or ()
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
        translations = set(getattr(aq_base(parent), "translations", ()) or ())
        translations.add(self.uuid)
        parent.translations = translations
        getPersistentTranslationCounter(self.context).change(1)

    def unregisterTranslation(self, parent):
        translations = set(getattr(aq_base(parent), "translations", ()) or ())
        translations.discard(self.uuid)
        parent.translations = translations
        getPersistentTranslationCounter(self.context).change(1)

    def clear(self):
        uuids = aq_base(self.context.translations)
        if uuids:
            items = map(self.resolve, uuids)
            self.context.translations = set()
            getPersistentTranslationCounter(self.context).change(1)
            return items

        return ()

    def detach(self):
        result = self.catalog(translations=self.uuid)
        if not result:
            return

        if len(result) > 1:
            logger.warn(
                "This object is contained in multiple translation graphs!"
            )

        obj = result[0].getObject()
        obj.translations = obj.translations - set((self.uuid, ))
        getPersistentTranslationCounter(self.context).change(1)
        return obj
