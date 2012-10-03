from zope.lifecycleevent import modified
from zope.schema.interfaces import ValidationError
from plone.uuid.interfaces import IUUID
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Acquisition import aq_base

from .interfaces import ITranslationGraph
from .interfaces import getLanguageIndependent
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
    modified(parent)


def objectModifiedEvent(context, event):
    """Handle event that content was modified.

    We need to copy language-independent fields to other content items
    in the translation graph.
    """

    translations = ITranslationGraph(context).getTranslations()
    items = [record[1] for record in translations]

    for field in getLanguageIndependent(context):
        name = field.__name__
        adapter = field.interface(context)

        try:
            value = getattr(adapter, name)
        except AttributeError:
            continue

        for item in items:
            adapter = field.interface(item)
            try:
                setattr(adapter, name, value)
            except ValidationError as exc:
                logger.warn(exc)


def objectRemovedEvent(context, event):
    """Handle event that content was removed.

    We need to remove the translation from its translation graph (if
    applicable).
    """

    container = event.oldParent
    wrapped = context.__of__(container)
    obj = ITranslationGraph(wrapped).removeTranslation()
    if obj is not None:
        modified(obj)
