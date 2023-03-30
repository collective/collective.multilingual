# -*- coding: utf-8 -*-

from plone.app.dexterity.behaviors.metadata import IDublinCore
from plone.autoform import interfaces as autoform
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import getAdditionalSchemata
from plone.supermodel.utils import mergedTaggedValueList
from z3c.form.interfaces import IForm
from zope import schema
from zope.component import getUtility
from zope.interface import Interface, provider
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

from .i18n import MessageFactory as _


def setLanguageIndependent(*fields):
    for field in fields:
        field.interface.setTaggedValue(
            LANGUAGE_INDEPENDENT_KEY,
            ((autoform.IAutoExtensibleForm, field.__name__, True),),
        )


def getLanguageIndependent(context):
    portal_type = context.portal_type
    fti = getUtility(IDexterityFTI, name=portal_type)

    schemata = getAdditionalSchemata(context=context, portal_type=portal_type)
    schemas = tuple(schemata) + (fti.lookupSchema(),)

    fields = set()
    for schema in schemas:
        entries = mergedTaggedValueList(schema, LANGUAGE_INDEPENDENT_KEY)
        for interface, name, value in entries:
            field = schema[name]
            fields.add(field)

    return fields


LANGUAGE_INDEPENDENT_KEY = "plone.autoform.languageindependent"


class IBrowserLayer(IDefaultBrowserLayer):
    """Add-on browser layer.

    This layer enables the user interface components.
    """


@provider(IFormFieldProvider)
class IMultilingual(Interface):
    """An item that supports translation into other languages."""

    translations = schema.Set(
        title=_("Translations"),
        description=_(
            "The items referenced in this field " "are the direct translations."
        ),
        required=False,
        value_type=schema.Choice(
            vocabulary="collective.multilingual.vocabularies.Translations",
        ),
    )


class ISettings(Interface):
    use_nearest_translation = schema.Bool(
        title=_("Contextual language selection"),
        description=_(
            "Select this option to use the nearest "
            "translation of the current content. For each "
            "supported language, the items in the parent list are "
            "checked in reverse order for a translation. "
            "If not selected, the language home page is "
            "used (if available)."
        ),
        default=True,
        required=False,
    )

    enable_catalog_patch = schema.Bool(
        title=_("Search current language only"),
        description=_(
            "Select this to configure the catalog to "
            "return only content in the "
            "current language. Note that items that do "
            "not have a language setting are exempt from "
            "this rule."
        ),
        default=True,
        required=False,
    )

    no_filter = schema.Set(
        title=_("Indexes that cancel language filtering"),
        description=_(
            "When a query contains a value for one of "
            "the indexes provided here, the current "
            "language will not be applied as a filter, "
            "even when the setting is enabled."
        ),
        default=set(["UID", "id", "getId", "path", "translations"]),
        value_type=schema.Choice(
            vocabulary="collective.multilingual.vocabularies.Indexes",
        ),
        required=False,
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

        For each language, a tuple is returned::

          (lang_id, obj, distance)

        The ``distance`` parameter corresponds to how many hops there
        are between the provided ``context`` and that for which there
        is a translation contained in the translation graph.

        If the distance is zero, then the translation is contained in
        the current translation graph: ``self``.

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

    def unregisterTranslation(parent):
        """Removes context as translation for the provided parent."""

    def clear():
        """Clear own translation references."""

    def detach():
        """Remove context from graph."""


IMultilingual.setTaggedValue(autoform.MODES_KEY, ((IForm, "translations", "hidden"),))

setLanguageIndependent(
    IDublinCore["contributors"],
    IDublinCore["creators"],
    IDublinCore["rights"],
)
