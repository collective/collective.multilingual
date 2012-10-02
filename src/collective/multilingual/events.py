from zope.lifecycleevent import modified
from plone.uuid.interfaces import IUUID
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
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

    if not IPloneSiteRoot.providedBy(container):
        language = aq_base(container).language
        if not context.language:
            context.language = language
            modified(context)

    catalog = getToolByName(container, 'portal_catalog')

    translations = getattr(aq_base(context), "translations", None)
    if not translations:
        return

    uuid = list(translations)[0]
    result = catalog(UID=uuid)
    if len(result) != 1:
        return

    del context.translations
    modified(context)

    parent = result[0].getObject()
    if parent.creation_date >= context.creation_date:
        logger.warn(
            "parent %r is newer than translation %r." % (
                uuid, str(IUUID(context)))
            )

    # Now, append the translation to the source item's list.
    wrapped = context.__of__(container)
    ITranslationGraph(wrapped).registerTranslation(parent)
    modified(parent)


def objectRemovedEvent(context, event):
    container = event.oldParent
    wrapped = context.__of__(container)
    obj = ITranslationGraph(wrapped).removeTranslation()
    if obj is not None:
        modified(obj)
