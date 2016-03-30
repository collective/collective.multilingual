# -*- coding: utf-8 -*-

from zope.interface import implements
from zope.interface import implementer
from zope.component import queryMultiAdapter
from zope.i18n import Message
from zope.i18nmessageid import MessageFactory

from z3c.form.interfaces import NO_VALUE
from z3c.form.interfaces import IValue

from plone.app.dexterity.behaviors.metadata import IDublinCore
from Products.CMFCore.utils import getToolByName
from Acquisition import aq_base

from ..interfaces import LANGUAGE_INDEPENDENT_KEY
from ..interfaces import IMultilingual


@implementer(IValue)
def adaptGroupFormWidgetValue(context, request, form, field, widget):
    return queryMultiAdapter(
        (context, request, form.parentForm, field, widget),
        IValue,
        name="default"
    )


def isLanguageIndependent(field):
    if field.interface is None:
        return False

    try:
        return field.interface.getTaggedValue(LANGUAGE_INDEPENDENT_KEY)
    except KeyError:
        return False


class ValueBase(object):
    implements(IValue)

    def __init__(self, context, request, form, field, widget):
        self.context = context
        self.request = request
        self.field = field
        self.form = form
        self.widget = widget

    @property
    def catalog(self):
        return getToolByName(self.context, 'portal_catalog')


class AddingLanguageIndependentValue(ValueBase):
    def getTranslationUuid(self):
        return self.request.form.get('translation')

    def getLanguageId(self):
        return self.request.form.get('language')

    def get(self):
        uuid = self.getTranslationUuid()

        if self.field is IMultilingual['translations']:
            return [uuid]

        if self.field is IDublinCore['language']:
            return self.getLanguageId()

        if isLanguageIndependent(self.field):
            result = self.catalog(UID=uuid)

            if len(result) == 1:
                obj = result[0].getObject()
                name = self.field.__name__
                try:
                    value = getattr(aq_base(obj), name)
                except AttributeError:
                    pass
                else:
                    return value

        if self.field.default is None:
            return NO_VALUE

        return self.field.default


class LanguageIndependentWidgetLabel(ValueBase):
    msgid = u"${label} \u2022"

    def get(self):
        label = self.widget.label

        if (isLanguageIndependent(self.field) and
            isinstance(label, Message) and
            label != self.msgid
        ):
            label = MessageFactory(label.domain)(
                self.msgid, mapping={'label': label}
            )

        return label
