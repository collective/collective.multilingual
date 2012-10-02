from Acquisition import aq_base
from plone.indexer import indexer
from .interfaces import IMultilingual

@indexer(IMultilingual)
def translations(obj):
    unwrapped = aq_base(obj)
    return getattr(unwrapped, "translations", set())

