from zope.security import checkPermission

from plone.app.i18n.locales.browser import selector
from plone.app.layout.navigation.defaultpage import isDefaultPage

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.interfaces import ISiteRoot

from ..interfaces import ITranslationGraph
from ..interfaces import IMultilingual


class LanguageSelector(selector.LanguageSelector):
    def getLanguageActions(self):
        entries = self.languages()

        if not IMultilingual.providedBy(self.context):
            return entries

        context = self.context.aq_inner
        parent = context.__parent__
        if isDefaultPage(parent, context):
            if not ISiteRoot.providedBy(parent):
                context = parent

        lang_items = ITranslationGraph(context).getNearestTranslations()

        translations = {}
        for lang_id, item, distance in lang_items:
            translations[lang_id] = item

        site = getToolByName(self.context, name="portal_url").getPortalObject()
        for entry in entries:
            lang_id = entry['code']
            obj = translations.get(lang_id)
            if obj is None:
                try:
                    obj = site[lang_id]
                except KeyError:
                    continue

            if not checkPermission("zope2.View", obj):
                continue

            entry['url'] = obj.absolute_url()

        return entries
