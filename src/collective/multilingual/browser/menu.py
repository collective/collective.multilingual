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
from ..interfaces import ITranslationGraph


class TranslateMenu(BrowserMenu):
    def getMenuItems(self, context, request):
        menu = []

        if not IUUIDAware.providedBy(context):
            return menu

        lt = getToolByName(context, 'portal_languages')
        showflags = lt.showFlags()
        uuid = str(IUUID(context))
        current_lang = getattr(aq_base(context), "language", "")
        default_lang = lt.getDefaultLanguage()
        display_languages = request.locale.displayNames.languages

        # 1. Get translation information for each supported language.
        lang_items = ITranslationGraph(context).getNearestTranslations()

        site = getToolByName(context, name="portal_url").getPortalObject()
        site_url = site.absolute_url()

        # 2. Convert items to menu actions.
        for lang_id, item, contained in lang_items:
            if lang_id == current_lang:
                continue

            if not current_lang and lang_id == default_lang:
                continue

            icon = showflags and lt.getFlagForLanguageCode(lang_id) or None

            display_lang_name = display_languages[lang_id]
            title = display_lang_name

            if contained:
                url = "/edit"
            else:
                url = "/++add++%s?%s" % (
                    context.portal_type,
                    urllib.urlencode({
                        'translation': uuid,
                        'language': lang_id,
                        }))

            # 3. Determine if we've got a translation target folder or
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

                        url = site_url + "/" + lang_id + url
                        url = "/@@setup-language?language=%s&next_url=%s" % (
                            lang_id, urllib.quote_plus(url))

                        action_url = site_url + url

            # 4. We've got a target folder, so just use the add-URL.
            if item is not None:
                action_url = item.absolute_url() + url

            entry = {
                "title": translate(title, context=request),
                "description": _(u"description_translate_into",
                                    default=u"Translate into ${lang_name}",
                                 mapping={"lang_name": display_lang_name}),
                "action": action_url,
                "selected": False,
                "icon": icon,
                "width": 14,
                "height": 11,
                "extra": {"id": "translate_into_%s" % lang_id,
                           "separator": None,
                           "class": ""},
                "submenu": None,
                }

            menu.append(entry)

        # 5. Sort.
        menu.sort(key=lambda item: unicode(item['title']))

        # 6. Add link to language controlpanel.
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
