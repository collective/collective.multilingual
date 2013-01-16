# -*- coding: utf-8 -*-

import urllib

from zope.component import getUtility
from zope.i18n import translate

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import ManagePortal

from Acquisition import aq_base

from zope.browsermenu.menu import BrowserMenu
from zope.browsermenu.menu import BrowserSubMenuItem

from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.interfaces import IDexterityFTI
from plone.memoize.instance import memoize
from plone.uuid.interfaces import IUUID
from plone.app.layout.navigation.defaultpage import isDefaultPage
from plone.app.layout.navigation.defaultpage import getDefaultPage
from plone.app.layout.navigation.interfaces import INavigationRoot

from ..i18n import MessageFactory as _
from ..interfaces import IBrowserLayer
from ..interfaces import ITranslationGraph


def getTranslationActionItems(context, request):
    """Return action menu items for 'Translate' menu."""

    parent = context.__parent__
    is_default_page = isDefaultPage(parent, context)

    # There is a special case here which is when the ``context`` is a
    # default page. In this case, we compute the nearest translations
    # of the parent folder, unless the parent is a navigation or site
    # root.
    use_parent = False

    graph = ITranslationGraph(context)
    
    current_lang = getattr(aq_base(context), "language", "")
    lt = getToolByName(context, 'portal_languages')
    pt = getToolByName(context, name="portal_url")
    showflags = lt.showFlags()
    default_lang = lt.getDefaultLanguage()
    display_languages = request.locale.displayNames.languages
    site = pt.getPortalObject()
    site_url = site.absolute_url()

    if use_parent:
        lang_items = ITranslationGraph(parent).getNearestTranslations()
    else:
        lang_items = graph.getNearestTranslations()

    menu = []
    for lang_id, item, distance in lang_items:
        if lang_id == current_lang:
            continue

        if not current_lang and lang_id == default_lang:
            continue

        icon = showflags and lt.getFlagForLanguageCode(lang_id) or None

        display_lang_name = display_languages[lang_id]
        title = unicode(display_lang_name)

        if use_parent:
            if distance >= 0:
                distance += 1

            if item is not None:
                default_page = getDefaultPage(item)
                if default_page is not None:
                    item = item[default_page]
                    distance = 0
                else:
                    add_context = context
            else:
                add_context = parent
        else:
            add_context = context

        # If the item already exists, link to its default view.
        if distance == 0:
            assert item is not None
            fti = getUtility(IDexterityFTI, name=item.portal_type)
            info = fti.getActionInfo('object/view')
            url = "/" + info['url']
            title += u" ✓"

        # Otherwise, link to the add form.
        else:
            uuid = str(IUUID(add_context))
            portal_type = add_context.portal_type
            title = _(u"${title} (add...)", mapping={'title': title})

            url = "/++add++%s?%s" % (
                portal_type,
                urllib.urlencode({
                    'translation': uuid,
                    'language': lang_id,
                }))

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

        if item is not None:
            action_url = item.absolute_url() + url.rstrip('/')

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

    menu.sort(key=lambda item: unicode(item['title']))

    if graph.getTranslations():
        menu.append({
            "title": _(u"Clear..."),
            "description": _(u"Clear the list of translation references."),
            "action": graph.context.absolute_url() + "/@@clear-translations",
            "selected": False,
            "icon": None,
            "extra": {"id": "clearTranslations",
                      "separator": None,
                      "class": ""},
            "submenu": None,
        })
    else:
        menu.append({
            "title": _(u"This is a translation of..."),
            "description": _(u"Mark this item as the translation for "
                             u"another content item on the site."),
            "action": graph.context.absolute_url() + "/@@set-translation-for",
            "selected": False,
            "icon": None,
            "extra": {"id": "setTranslationFor",
                      "separator": None,
                      "class": ""},
            "submenu": None,
        })

    return menu


class TranslateMenu(BrowserMenu):
    def getMenuItems(self, context, request):
        if not IDexterityContent.providedBy(context):
            return []

        items = getTranslationActionItems(context, request)

        # 6. Add link to language controlpanel.
        site = getToolByName(context, name="portal_url").getPortalObject()
        mt = getToolByName(context, "portal_membership")
        if mt.checkPermission(ManagePortal, site):
            items.append({
                "title": _(u"title_language_settings",
                           default=u"Language settings..."),
                "description": _(u"description_language_settings",
                                 default=u""),
                "action": site.absolute_url() + "/@@language-controlpanel",
                "selected": False,
                "icon": None,
                "extra": {"id": "_language_settings",
                          "separator": None,
                          "class": ""},
                "submenu": None,
            })

        return items


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
        if INavigationRoot.providedBy(self.context):
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
