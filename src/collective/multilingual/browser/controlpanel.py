import collections
import itertools

from Acquisition import ImplicitAcquisitionWrapper
from plone.app.registry.browser import controlpanel
from plone.dexterity.interfaces import IDexterityFTI
from plone.registry.interfaces import IRegistry
from plone.registry.recordsproxy import RecordsProxy
from plone.z3cform import layout
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from zope import schema
from zope.component import getSiteManager, getUtility
from zope.interface import implementer, providedBy
from zope.lifecycleevent import modified

from ..i18n import MessageFactory as _
from ..interfaces import IMultilingual, ISettings
from ..utils import dottedName, getPersistentTranslationCounter

_stat = collections.namedtuple("stat", ("language", "count", "ratio"))


def settingsModified(context, event):
    getPersistentTranslationCounter(context.context).change(1)


class IControlPanelSchema(ISettings):
    ftis = schema.Set(
        title=_("Content types"),
        description=_(
            "Select which content types should support "
            "content in multiple content (the "
            '"Multilingual" behavior).'
        ),
        required=False,
        value_type=schema.Choice(
            vocabulary="collective.multilingual.vocabularies.FTIs"
        ),
    )


@implementer(IControlPanelSchema)
class ControlPanelAdapter(object):

    _behavior_name = dottedName(IMultilingual)

    context = None
    proxy = None

    def __init__(self, context):
        self.__dict__["context"] = context
        self.__dict__["proxy"] = RecordsProxy(getUtility(IRegistry), ISettings)

    def _get_ftis(self):
        sm = getSiteManager(self.context)
        ftis = []
        for fti in sm.getAllUtilitiesRegisteredFor(IDexterityFTI):
            if self._behavior_name in fti.behaviors:
                ftis.append(fti)

        return ftis

    def _set_ftis(self, ftis):
        previous = set(self._get_ftis())
        for fti in ftis:
            previous.discard(fti)

            if self._behavior_name in fti.behaviors:
                continue

            fti.behaviors = list(fti.behaviors)
            fti.behaviors.append(self._behavior_name)
            modified(fti)

        for fti in previous:
            fti.behaviors.remove(self._behavior_name)
            modified(fti)

    ftis = property(_get_ftis, _set_ftis)

    def __getattr__(self, name):
        return getattr(self.proxy, name)

    def __setattr__(self, name, value):
        if providedBy(self.proxy).get(name) is None:
            object.__setattr__(self, name, value)
        else:
            setattr(self.proxy, name, value)


class ControlPanelEditForm(controlpanel.RegistryEditForm):
    schema = IControlPanelSchema
    template = ViewPageTemplateFile("templates/control-panel.pt")

    label = _("Settings for content in multiple languages")
    description = _(
        'Add or remove the "Multilingual" behavior from your '
        "content types, and view translation statistics."
    )

    def getContent(self):
        return ImplicitAcquisitionWrapper(
            ControlPanelAdapter(self.context), self.context
        )

    def getDefaultLanguage(self):
        lt = getToolByName(self.context, "portal_languages")
        default_lang = lt.getDefaultLanguage()
        return self.getDisplayLanguage(default_lang)

    def getDisplayLanguage(self, lang_id):
        lang = lang_id.split("-")[0]
        return self.request.locale.displayNames.languages[lang]

    def getLanguageStats(self):
        """Return list of language statistics."""

        lt = getToolByName(self.context, "portal_languages")
        supported = lt.listSupportedLanguages()

        stats = []
        total = 0

        catalog = getToolByName(self.context, "portal_catalog")

        if "Language" not in catalog.indexes():
            IStatusMessage(self.request).addStatusMessage(
                _("Catalog does not have a language index."), type="warning"
            )
            return ()

        for lang_id in dict(supported):
            items = catalog(language=lang_id)
            count = len(items)
            total += count

            stats.append((lang_id, count))

        total += len(catalog(language=""))

        # An edge-case: there is no content :-).
        if not total:
            return ()

        result = [
            (
                self.getDisplayLanguage(lang_id),
                count,
                "%1.f%%" % (100 * count / float(total)),
            )
            for (lang_id, count) in stats
        ]

        result.sort()
        result.insert(0, (_("Any"), total, "100%"))

        return tuple(itertools.starmap(_stat, result))


ControlPanel = layout.wrap_form(
    ControlPanelEditForm, controlpanel.ControlPanelFormWrapper
)
