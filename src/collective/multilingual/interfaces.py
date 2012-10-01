# -*- coding: utf-8 -*-

from zope import schema
from zope.interface import Interface
from zope.interface import alsoProvides

from plone.app.dexterity.behaviors.metadata import IDublinCore
from plone.autoform.interfaces import IFormFieldProvider
from plone.autoform import interfaces as autoform

from z3c.form.interfaces import IAddForm

from .i18n import MessageFactory as _


def setLanguageIndependent(*fields):
    for field in fields:
        field.interface.setTaggedValue(
            LANGUAGE_INDEPENDENT_KEY, (
                (autoform.IAutoExtensibleForm, field.__name__, True),
                ))

LANGUAGE_INDEPENDENT_KEY = u"plone.autoform.languageindependent"


class IBrowserLayer(Interface):
    """Add-on browser layer.

    This layer enables the user interface components.
    """


class IMultilingual(Interface):
    """An item that supports translation into other languages."""

    translations = schema.Set(
        title=_(u"Translations"),
        description=_(u"The items referenced in this field "
                      u"are the direct translations."),
        required=False,
        value_type=schema.Choice(
            vocabulary="collective.multilingual.vocabularies.Translations",
            )
        )


class ITranslationGraph(Interface):
    """Represents the translation graph for a translated content item."""

    def getCanonical():
        """Return the canonical content item.

        This method walks up the translation graph (using the catalog)
        to determine the root item which is the canonical content.
        """

    def getParent():
        """Return the parent translation.

        This is the object which has a direct translation relationship
        to the context.
        """

    def getTranslations():
        """Return all content items in translation graph.

        Note that the current context is omitted from the result.
        """

    def registerTranslation(parent):
        """Register context as translation for the provided parent."""

    def removeTranslation():
        """Remove context from graph."""


alsoProvides(IMultilingual, IFormFieldProvider)

IMultilingual.setTaggedValue(
    autoform.MODES_KEY, (
        (IAddForm, 'translations', 'hidden'),
        ))

setLanguageIndependent(
    IDublinCore['contributors'],
    IDublinCore['creators'],
    IDublinCore['rights'],
    )
