from Products.CMFPlone.CatalogTool import CatalogTool
from Products.CMFCore.utils import getToolByName

from .utils import logger
from .interfaces import IBrowserLayer

_searchResults = CatalogTool.searchResults
_noFilter = set(('UID', 'id', 'getId', 'translations'))
_marker = object()


def applyLanguageFilter(site, request, kw):
    lt = getToolByName(site, 'portal_languages', None)
    if lt is None:
        return

    for query in (request, kw):
        if query is not None:
            if set(query) & _noFilter:
                return

            language = query.pop('Language', _marker)
            if language == 'all':
                return

            if language is _marker:
                language = query.get('language', _marker)
                if language is not _marker:
                    if language == 'all':
                        del query['language']

                    return
            else:
                query['language'] = language

            if 'path' in query:
                return

    language = lt.getPreferredLanguage()
    if language == lt.getDefaultLanguage():
        default = u""
    else:
        default = None

    query['language'] = (language, default)

    # XXX: For path queries that target a path under a language
    # folder, and if we want to support a list of (language-neutral)
    # shared or common folders, this would be the place to customize
    # the path query to include these. This might be an images folder.


def searchResults(self, REQUEST=None, **kw):
    for request in (REQUEST, getattr(self, "REQUEST", None)):
        if request is not None and IBrowserLayer.providedBy(request):
            applyLanguageFilter(self, REQUEST, kw)
            break

    return _searchResults(self, REQUEST, **kw)

CatalogTool.searchResults = searchResults
CatalogTool.__call__ = searchResults
logger.info("patched catalog tool to filter on current language.")
