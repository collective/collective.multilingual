import logging

from Products.CMFCore.utils import getToolByName
from BTrees.Length import Length
from zope.annotation.interfaces import IAnnotations

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
