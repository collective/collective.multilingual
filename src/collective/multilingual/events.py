from zope.lifecycleevent import modified
from zope.schema.interfaces import ValidationError
from plone.uuid.interfaces import IUUID
from plone.app.layout.navigation.defaultpage import getDefaultPage
from plone.app.layout.navigation.defaultpage import isDefaultPage
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Acquisition import aq_base

from .interfaces import ITranslationGraph
from .interfaces import getLanguageIndependent
from .utils import logger
from .utils import getPersistentTranslationCounter


def objectAddedEvent(context, event):
    """Handle event that translation was added.

    By convention, when a translation is created, its ``translations``
    attribute is set to a list with a single item, which is the
    translation source.

    In this event handler, we simply reverse that relationship.
    """

    container = event.newParent

    # If we're copying an item, than we can expect a volatile
    # attribute to contain a reference to the original item. This
    # information is turned into a translation reference below.
    try:
        uuid, language = context._v_multilingual_copy
    except AttributeError:
        is_copy = False
        translations = getattr(aq_base(context), "translations", None)
        if translations:
            uuid = list(translations)[0]
            del context.translations
        else:
            uuid = None
    else:
        # The Plone site root is a special case, because it always has
        # a language setting, so the check below won't work.
        if IPloneSiteRoot.providedBy(container):
            return

        # If we're copying the item into the same language, then we do
        # nothing.
        if language == getattr(aq_base(container), "language"):
            return

        is_copy = True

    # Inherit the language of the container to which the item is
    # added.
    if not IPloneSiteRoot.providedBy(container):
        if not context.language:
            context.language = aq_base(container).language

    catalog = getToolByName(container, 'portal_catalog')
    result = catalog(UID=uuid)
    if len(result) != 1:
        return

    parent = result[0].getObject()
    if not is_copy and parent.creation_date >= context.creation_date:
        logger.warn(
            "parent %r is newer than translation %r." % (
                uuid, str(IUUID(context)))
        )

    # If the item being copied or translated was a default page, apply
    # the same setting to this item, relative to its container.
    if getDefaultPage(container) is None:
        if isDefaultPage(parent.__parent__, parent):
            objectId = context.getId()
            container.setDefaultPage(objectId)
            modified(container)

    # If this item is being copied into a language folder, make sure
    # we unregister an existing translation.
    if is_copy:
        for language, obj in ITranslationGraph(parent).getTranslations():
            if language == container.language:
                ITranslationGraph(obj).unregisterTranslation(parent)

    # Now, append the translation to the source item's list.
    wrapped = context.__of__(container)
    ITranslationGraph(wrapped).registerTranslation(parent)
    modified(parent)

    # For technical reasons, we need to invalidate the counter
    # explicitly because the item being added might not yet be
    # catalogued.
    getPersistentTranslationCounter(parent).change(1)


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
    obj = ITranslationGraph(wrapped).detach()
    if obj is not None:
        modified(obj)


def objectCopiedEvent(context, event):
    """Handle event that content was copied."""

    context._v_multilingual_copy = (
        IUUID(event.original), getattr(
            aq_base(event.original), "language",
        ))

    # Copies never have translations!
    context.__dict__.pop('translations', None)
