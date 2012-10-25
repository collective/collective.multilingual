from zope.security import checkPermission
from zope.component import ComponentLookupError

from plone.memoize.view import memoize
from plone.app.i18n.locales.browser import selector
from plone.app.layout.navigation.defaultpage import isDefaultPage
from plone.app.layout.navigation.interfaces import INavigationRoot

from Products.CMFCore.utils import getToolByName

from ..interfaces import ITranslationGraph
from ..interfaces import IMultilingual
from ..utils import getSettings


class LanguageSelector(selector.LanguageSelector):
    def available(self):
        actions = self.getLanguageActions()
        return len(actions) > 0

    @memoize
    def getLanguageActions(self):
        site = getToolByName(self.context, name="portal_url").getPortalObject()

        lt = getToolByName(self.context, 'portal_languages')
        default_lang = lt.getDefaultLanguage()

        entries = self.languages()
        mappings = [site, {
            default_lang: site,
        }]

        try:
            settings = getSettings(site)
        except ComponentLookupError:
            pass
        else:
            if settings.use_nearest_translation:
                if IMultilingual.providedBy(self.context):
                    translations = self.getTranslations()
                    mappings.insert(0, translations)

        return self.mapEntries(entries, *mappings)

    def getTranslations(self):
        context = self.context.aq_inner
        parent = context.__parent__
        if isDefaultPage(parent, context):
            if not INavigationRoot.providedBy(parent):
                context = parent

        lang_items = ITranslationGraph(context).getNearestTranslations()

        translations = {}
        for lang_id, item, distance in lang_items:
            if item is None:
                continue

            parent = item.__parent__
            if isDefaultPage(parent, item):
                item = parent

            translations[lang_id] = item

        return translations

    def mapEntries(self, entries, *mappings):
        result = []
        for entry in entries:
            lang_id = entry['code']

            for mapping in mappings:
                obj = mapping.get(lang_id)
                if obj is not None:
                    if checkPermission("zope2.View", obj):
                        entry['url'] = obj.absolute_url()
                        result.append(entry)
                        break

        return result
