# -*- coding: utf-8 -*-

import itertools

from zope import schema
from zope.interface import Interface
from zope.interface import alsoProvides
from zope.component import getUtility

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import getAdditionalSchemata
from plone.app.dexterity.behaviors.metadata import IDublinCore
from plone.autoform.interfaces import IFormFieldProvider
from plone.autoform import interfaces as autoform
from plone.supermodel.utils import mergedTaggedValueList

from z3c.form.interfaces import IAddForm

from .i18n import MessageFactory as _


def setLanguageIndependent(*fields):
    for field in fields:
        field.interface.setTaggedValue(
            LANGUAGE_INDEPENDENT_KEY, (
                (autoform.IAutoExtensibleForm, field.__name__, True),
                ))


def getLanguageIndependent(context):
    portal_type = context.portal_type
    fti = getUtility(IDexterityFTI, name=portal_type)

    schemata = getAdditionalSchemata(context=context, portal_type=portal_type)
    schemas = tuple(schemata) + (fti.lookupSchema(), )

    fields = set()
    for schema in schemas:
        entries = mergedTaggedValueList(schema, LANGUAGE_INDEPENDENT_KEY)
        for interface, name, value in entries:
            field = schema[name]
            fields.add(field)

    return fields


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

    def getNearestTranslations(self):
        """Return nearest translations for all supported languages.

        For each language, a tuple ``(lang_id, item, contained)`` is
        returned, where ``item`` is the nearest item translated into
        the specified language in the parent chain of the canonical
        content item, and ``contained`` is true if the item is
        contained in the current translation graph.

        Note that the context is omitted from the result.
        """

    def getParent():
        """Return the parent translation.

        This is the object which has a direct translation relationship
        to the context. If no such object exists, no return value is
        provided.
        """

    def getTranslations():
        """Return all content items in translation graph.

        Note that the context is omitted from the result.
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