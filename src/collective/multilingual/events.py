from plone.uuid.interfaces import IUUID
from Products.CMFCore.utils import getToolByName
from Acquisition import aq_base

from .interfaces import ITranslationGraph
from .utils import logger


def objectAddedEvent(context, event):
    """Handle event that translation was added.

    By convention, when a translation is created, its ``translations``
    attribute is set to a list with a single item, which is the
    translation source.

    In this event handler, we simply reverse that relationship.
    """

    container = event.newParent
    catalog = getToolByName(container, 'portal_catalog')

    translations = getattr(aq_base(context), "translations", None)
    if not translations:
        return

    uuid = list(translations)[0]
    result = catalog(UID=uuid)
    if len(result) != 1:
        return

    del context.translations

    parent = result[0].getObject()
    if parent.creation_date >= context.creation_date:
        logger.warn(
            "parent %r is newer than translation %r." % (
                uuid, str(IUUID(context)))
            )

    # Now, append the translation to the source item's list.
    wrapped = context.__of__(container)
    ITranslationGraph(wrapped).registerTranslation(parent)


def objectRemovedEvent(context, event):
    container = event.oldParent
    wrapped = context.__of__(container)
    ITranslationGraph(wrapped).removeTranslation()
