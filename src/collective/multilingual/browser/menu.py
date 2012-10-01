# -*- coding: utf-8 -*-

import urllib

from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.i18n import translate

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.permissions import ManagePortal
from Acquisition import aq_base

from zope.browsermenu.menu import BrowserMenu
from zope.browsermenu.menu import BrowserSubMenuItem

from plone.memoize.instance import memoize
from plone.uuid.interfaces import IUUID
from plone.uuid.interfaces import IUUIDAware


from ..i18n import MessageFactory as _
from ..interfaces import IBrowserLayer
from ..interfaces import IMultilingual
from ..interfaces import ITranslationGraph


class TranslateMenu(BrowserMenu):
    def getMenuItems(self, context, request):
        menu = []

        if not IUUIDAware.providedBy(context):
            return menu

        lt = getToolByName(context, 'portal_languages')
        supported = lt.listSupportedLanguages()
        assert len(supported) > 1

        langs = dict(supported)
        showflags = lt.showFlags()
        uuid = str(IUUID(context))
        current_lang = getattr(aq_base(context), "language", "")

        # Build list of translation target folders. That is, for each
        # supported language, determine whether we've already got a
        # translation, or a folder where we can create one.
        folder = context
        lang_items = []

        default_lang = lt.getDefaultLanguage()
        display_languages = request.locale.displayNames.languages

        # 1. Determine existing translations.
        for lang_id, item in ITranslationGraph(context).getTranslations():
            if not lang_id:
                lang_id = default_lang

            try:
                lang_name = langs.pop(lang_id)
            except KeyError:
                # Appearently, this language is no longer
                # supported. Ignore it!
                continue

            lang_items.append((lang_id, lang_name, item, True))

        # 2. Look for parent folder translations.
        context_state = getMultiAdapter(
            (context, request), name=u"plone_context_state"
            )

        folder = context_state.folder()
        if IMultilingual.providedBy(folder):
            for lang_id, item in ITranslationGraph(folder).getTranslations():
                try:
                    lang_name = langs.pop(lang_id)
                except KeyError:
                    continue

                lang_items.append((lang_id, lang_name, folder, False))

        # 3. Process remaining supported languages.
        site = getToolByName(context, name="portal_url").getPortalObject()
        for lang_id, lang_name in langs.items():
            lang_items.append((lang_id, lang_name, None, False))

        # 4. Convert items to menu actions.
        for lang_id, lang_name, item, exists in lang_items:
            if lang_id == current_lang:
                continue

            if not current_lang and lang_id == default_lang:
                continue

            icon = showflags and lt.getFlagForLanguageCode(lang_id) or None

            display_lang_name = display_languages.get(lang_id, lang_name)
            title = display_lang_name

            if exists:
                url = "/edit"
            else:
                url = "/++add++%s?%s" % (
                    context.portal_type,
                    urllib.urlencode({
                        'translation': uuid,
                        'language': lang_id,
                        }))

            # 2. Determine if we've got a translation target folder or
            #    if we need to first ask user to set up the top-level
            #    language folder.
            if item is None:
                if lang_id == default_lang:
                    item = site
                else:
                    try:
                        item = site[lang_id]
                    except KeyError:
                        title = _(u"${lang_name} (setup required)",
                                  mapping={'lang_name': title})

                        url = folder.absolute_url() + "/" + lang_id + url
                        url = "/@@setup-language?language=%s&next_url=%s" % (
                            lang_id, urllib.quote_plus(url))

                        item = site

            # 3. We've got a target folder, so just use the add-URL.
            if item is not None:
                action_url = item.absolute_url() + url

            item = {
                "title": translate(title, context=request),
                "description": _(u"description_translate_into",
                                    default=u"Translate into ${lang_name}",
                                 mapping={"lang_name": display_lang_name}),
                "action": action_url,
                "selected": False,
                "icon": icon,
                "extra": {"id": "translate_into_%s" % lang_id,
                           "separator": None,
                           "class": ""},
                "submenu": None,
                }

            menu.append(item)

        # 5. Sort.
        menu.sort(key=lambda item: unicode(item['title']))

        # langs = translated_languages(context)
        # urls = translated_urls(context)
        # for lang in langs:
        #     lang_name = lang.title
        #     lang_id = lang.value
        #     icon = showflags and lt.getFlagForLanguageCode(lang_id) or None
        #     item = {
        #         "title": lang_name,
        #         "description": _(u"description_babeledit_menu",
        #                             default=u"Babel edit ${lang_name}",
        #                             mapping={"lang_name": lang_name}),
        #         "action": urls.getTerm(lang_id).title + "/babel_edit",
        #         "selected": False,
        #         "icon": icon,
        #         "extra": {"id": "babel_edit_%s" % lang_id,
        #                    "separator": None,
        #                    "class": ""},
        #         "submenu": None,
        #         }

        #     menu.append(item)

        # menu.append({
        #     "title": _(u"title_add_translations",
        #                default=u"Add translations..."),
        #     "description": _(u"description_add_translations",
        #                         default=u""),
        #     "action": url + "/add_translations",
        #     "selected": False,
        #     "icon": None,
        #     "extra": {"id": "_add_translations",
        #                "separator": langs and "actionSeparator" or None,
        #                "class": ""},
        #     "submenu": None,
        #     })

        # menu.append({
        #     "title": _(u"title_remove_translations",
        #                default=u"Remove translations..."),
        #     "description": _(
        #         u"description_remove_translations",
        #         default=u"Delete translations or remove the relations"),
        #     "action": url + "/remove_translations",
        #     "selected": False,
        #     "icon": None,
        #     "extra": {"id": "_remove_translations",
        #                "separator": langs and "actionSeparator" or None,
        #                "class": ""},
        #     "submenu": None,
        #     })

        site = getUtility(ISiteRoot)
        mt = getToolByName(context, "portal_membership")
        if mt.checkPermission(ManagePortal, site):
            portal_state = getMultiAdapter((context, request),\
                name="plone_portal_state")

            menu.append({
                "title": _(u"title_language_settings",
                           default=u"Language settings..."),
                "description": _(u"description_language_settings",
                                   default=u""),
                "action": portal_state.portal_url() + \
                          "/@@language-controlpanel",
                "selected": False,
                "icon": None,
                "extra": {"id": "_language_settings",
                          "separator": None,
                          "class": ""},
                "submenu": None,
                })

        return menu


class TranslateSubMenuItem(BrowserSubMenuItem):
    title = _(u"label_translate_menu", default=u"Translate")
    description = _(u"title_translate_menu",
                    default="Manage translations for your content.")
    submenuId = "plone_contentmenu_multilingual"
    order = 5
    extra = {"id": "plone-contentmenu-multilingual"}

    @property
    def action(self):
        return self.context.absolute_url() + "/@@manage-translations"

    @memoize
    def available(self):
        if not IBrowserLayer.providedBy(self.request):
            return False

        lt = getToolByName(self.context, 'portal_languages', None)
        if lt is None:
            return False

        supported = lt.listSupportedLanguages()
        if len(supported) < 2:
            return False

        return True

    def selected(self):
        return False
