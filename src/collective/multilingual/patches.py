from Products.CMFPlone.CatalogTool import CatalogTool
from Products.CMFCore.utils import getToolByName

from .utils import logger
from .interfaces import IBrowserLayer

_searchResults = CatalogTool.searchResults
_no_filter = set(('UID', 'id', 'getId'))


def applyLanguageFilter(site, query):
    # Accept both capitalized and lowercase language parameter.
    language = query.pop('language', None) or query.pop('Language', None)
    if language is not None:
        # The string 'all' short-circuits.
        if language != 'all':
            query['language'] = language

        return

    if set(query) & _no_filter:
        return

    lt = getToolByName(site, 'portal_languages', None)
    if lt is None:
        return

    language = lt.getPreferredLanguage()
    if language == lt.getDefaultLanguage():
        language = (language, u"")

    query['language'] = language

    # XXX: For path queries that target a path under a language
    # folder, and if we want to support a list of (language-neutral)
    # shared or common folders, this would be the place to customize
    # the path query to include these. This might be an images folder.


def searchResults(self, REQUEST=None, **kw):
    for req in (REQUEST, getattr(self, "REQUEST", None)):
        if req is not None and IBrowserLayer.providedBy(req):
            if REQUEST is not None and kw.get('Language', '') != 'all':
                query = REQUEST
            else:
                query = kw

            applyLanguageFilter(self, query)
            break

    return _searchResults(self, REQUEST, **kw)

CatalogTool.searchResults = searchResults
CatalogTool.__call__ = searchResults
logger.info("patched catalog tool to filter on current language.")
