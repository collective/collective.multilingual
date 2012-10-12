import logging

from Products.CMFCore.utils import getToolByName

logger = logging.getLogger("multilingual")


def dottedName(interface):
    return "%s.%s" % (interface.__module__, interface.__name__)


def getObjectByuuid(context, uuid):
    catalog = getToolByName(context, 'portal_catalog')
    result = catalog(UID=uuid)

    if len(result) != 1:
        return

    return result[0].getObject()
