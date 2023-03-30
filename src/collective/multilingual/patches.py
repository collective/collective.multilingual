from .interfaces import IBrowserLayer
from .utils import getSettings
from .utils import logger
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.CatalogTool import CatalogTool
from zope.component import ComponentLookupError

LANGUAGE_INDEX_NAME = "Language"

_searchResults = CatalogTool.searchResults
_marker = object()


def applyLanguageFilter(site, blacklist, request, kw):
    lt = getToolByName(site, "portal_languages", None)
    if lt is None:
        return

    for query in (request, kw):
        if query is not None:
            language = query.pop(LANGUAGE_INDEX_NAME, _marker)
            if language == "all":
                return

            path_query = query.get("path")
            if isinstance(path_query, dict) and path_query == {"query": ""}:
                query.pop("path")

            if language is _marker:
                language = query.get(LANGUAGE_INDEX_NAME, _marker)
                if language is not _marker:
                    if language == "all":
                        del query[LANGUAGE_INDEX_NAME]

                    return
            else:
                query[LANGUAGE_INDEX_NAME] = language

            if set(query) & blacklist:
                return

    language = lt.getPreferredLanguage()
    if language == lt.getDefaultLanguage():
        default = u""
    else:
        default = None

    query[LANGUAGE_INDEX_NAME] = (language, default)

    # XXX: For path queries that target a path under a language
    # folder, and if we want to support a list of (language-neutral)
    # shared or common folders, this would be the place to customize
    # the path query to include these. This might be an images folder.


def searchResults(self, REQUEST=None, **kw):
    for request in (REQUEST, getattr(self, "REQUEST", None)):
        if request is not None and IBrowserLayer.providedBy(request):
            site = self.portal_url.getPortalObject()

            try:
                settings = getSettings(site)
            except ComponentLookupError:
                break

            if settings.enable_catalog_patch:
                applyLanguageFilter(site, settings.no_filter, REQUEST, kw)

            break

    return _searchResults(self, REQUEST, **kw)


CatalogTool.searchResults = searchResults
CatalogTool.__call__ = searchResults
logger.info("patched catalog tool to filter on current language.")
