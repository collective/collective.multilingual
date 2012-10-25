import logging

from zope.annotation.interfaces import IAnnotations
from zope.component import ComponentLookupError

from plone.registry.interfaces import IRegistry

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import log_exc
from BTrees.Length import Length

from .interfaces import ISettings

logger = logging.getLogger("multilingual")

COUNTER = "collective.multilingual.counter"


def dottedName(interface):
    return "%s.%s" % (interface.__module__, interface.__name__)


def getObjectByuuid(context, uuid):
    catalog = getToolByName(context, 'portal_catalog')
    result = catalog(UID=uuid)

    if len(result) != 1:
        return

    return result[0].getObject()


def getPersistentTranslationCounter(self):
    site = getToolByName(self, 'portal_url').getPortalObject()
    annotations = IAnnotations(site)
    try:
        length = annotations[COUNTER]
    except KeyError:
        length = annotations[COUNTER] = Length()

    return length


def getSettings(site):
    registry = site.getSiteManager().getUtility(IRegistry)

    try:
        return registry.forInterface(ISettings)
    except:
        log_exc()
        raise ComponentLookupError(ISettings)
