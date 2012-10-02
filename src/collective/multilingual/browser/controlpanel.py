import collections
import itertools

from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage

from zope.interface import Interface

from plone.z3cform import layout
from plone.app.registry.browser import controlpanel

from ..i18n import MessageFactory as _


_stat = collections.namedtuple("stat", ("language", "count", "ratio"))


class ControlPanelEditForm(controlpanel.RegistryEditForm):
    schema = Interface
    template = ViewPageTemplateFile("templates/control-panel.pt")

    label = _(u"Multilingual")
    description = _(u"Statistics for content in multiple languages.")

    def updateActions(self):
        super(ControlPanelEditForm, self).updateActions()

        # We don't actually have any settings yet.
        del self.actions['save']
        del self.actions['cancel']

    def getDefaultLanguage(self):
        lt = getToolByName(self.context, 'portal_languages')
        default_lang = lt.getDefaultLanguage()
        return self.getDisplayLanguage(default_lang)

    def getDisplayLanguage(self, lang_id):
        return self.request.locale.displayNames.languages[lang_id]

    def getLanguageStats(self):
        """Return list of language statistics."""

        lt = getToolByName(self.context, 'portal_languages')
        supported = lt.listSupportedLanguages()

        stats = []
        total = 0

        catalog = getToolByName(self.context, 'portal_catalog')

        if 'language' not in catalog.indexes():
            IStatusMessage(self.request).addStatusMessage(
                _(u"Catalog does not have a language index."),
                type="warning")
            return ()

        for lang_id in dict(supported):
            items = catalog(language=lang_id)
            count = len(items)
            total += count

            stats.append((lang_id, count))

        total += len(catalog(language=u""))

        result = [
            (self.getDisplayLanguage(lang_id), count, "%1.f%%" % (
                100 * count / float(total)))
            for (lang_id, count) in stats
            ]

        result.sort()
        result.insert(0, (_(u"Any"), total, u"100%"))

        return tuple(itertools.starmap(_stat, result))


ControlPanel = layout.wrap_form(
    ControlPanelEditForm,
    controlpanel.ControlPanelFormWrapper
    )
