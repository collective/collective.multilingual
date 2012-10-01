import logging

from Products.CMFCore.utils import getToolByName

logger = logging.getLogger("multilingual")


def getObjectByuuid(context, uuid):
    catalog = getToolByName(context, 'portal_catalog')
    result = catalog(UID=uuid)

    if len(result) != 1:
        return

    return result[0].getObject()
