from .interfaces import IMultilingual
from Acquisition import aq_base
from plone.indexer import indexer


@indexer(IMultilingual)
def translations(obj):
    unwrapped = aq_base(obj)
    return set(getattr(unwrapped, "translations", ()) or ())


@indexer(IMultilingual)
def language(obj):
    unwrapped = aq_base(obj)
    return getattr(unwrapped, "language", None)
