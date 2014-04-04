from zope.interface import implements
from zope.interface import alsoProvides
from zope.interface import Interface
from zope import schema
from zope.i18n import translate
from zope.event import notify
from zope.lifecycleevent import modified

from z3c.form.form import Form
from z3c.form.interfaces import NO_VALUE
from z3c.form.interfaces import IValue
from z3c.form import button
from z3c.form import field
from z3c.relationfield.schema import RelationChoice

from plone.dexterity.utils import createContentInContainer
from plone.formwidget.contenttree import ObjPathSourceBinder
from plone.app.dexterity.behaviors.metadata import IBasic
from plone.app.dexterity.behaviors.exclfromnav import IExcludeFromNavigation
from plone.app.layout.navigation.interfaces import INavigationRoot

from Acquisition import aq_base

from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage

from ..i18n import MessageFactory as _
from ..interfaces import ITranslationGraph

language = field.Field(schema.ASCIILine(__name__="language"), mode="hidden")
next_url = field.Field(schema.ASCIILine(__name__="next_url"), mode="hidden")
interface_name = 'collective.multilingual.interfaces.IMultilingual'


class IAdding(Interface):
    fti = schema.Choice(
        title=_(u"Content type"),
        description=_(u"Select the content type to create and use "
                      u"as the language root folder."),
        required=True,
        vocabulary="collective.multilingual.vocabularies.ContainerFTIs"
    )

    schema.ASCIILine()


class IClearTranslations(Interface):
    pass


class ISelectTranslation(Interface):
    target = RelationChoice(
        title=_(u"Item"),
        description=_(u"Select the item that is a translation."),
        required=True,
        source=ObjPathSourceBinder(
            navigation_tree_query={
                'object_provides': interface_name,
            }
        ),
    )


class SetupFormDefaults(object):
    implements(IValue)

    def __init__(self, *args):
        self.get = lambda args=args: self.get_default(*args)

    @staticmethod
    def get_default(context, request, form, field, widget):
        value = None

        if field is IAdding['fti']:
            catalog = getToolByName(context, 'portal_catalog')
            values = catalog.Indexes['portal_type'].uniqueValues(
                withLengths=True)
            lengths = dict(values)

            # For the FTI, we return a default value of that FTI for
            # which there's the highest usage count (i.e. number of
            # content items). This is just a heuristic to try and get
            # a good default --- hopefully the "standard" folder type!
            highest = 0
            for term in widget.terms:
                fti = term.value
                item_count = lengths.get(fti.getId(), 0)

                if item_count > highest:
                    value = fti
                    highest = item_count
        else:
            lang_name = form.getLanguage()[1]

            if field is IBasic['title']:
                value = lang_name

            if field is IBasic['description']:
                message = _(
                    u"This folder contains content in ${lang_name}.",
                    mapping={'lang_name': lang_name})

                value = translate(message, context=request)

        # URL-parameters (hidden fields).
        if value is None:
            value = request.form.get(field.__name__, NO_VALUE)

        return value


class SetupLanguageView(Form):
    fields = (field.Fields(IBasic) +
              field.Fields(IAdding) +
              field.Fields(next_url, language))

    ignoreContext = True

    label = _(u"Create language folder")

    @property
    def description(self):
        lang_id, lang_name = self.getLanguage()
        return _(u"Submit this form to create a new folder for content "
                 u"in ${lang_name}. It will be added to "
                 u"your site root as \"/${lang_id}\".",
                 mapping={'lang_id': lang_id, 'lang_name': lang_name})

    def getLanguage(self):
        lang_id = self.request.form.get(
            'language', self.request.form.get('form.widgets.language')
        )
        lang_name = self.request.locale.displayNames.languages[lang_id]
        return lang_id, lang_name

    @button.buttonAndHandler(_(u'Create'))
    def handleCreate(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = _("Please correct errors.")
            return

        lang_id = data['language']
        fti = data['fti']

        folder = createContentInContainer(
            self.context, fti.getId(), id=lang_id,
        )

        # It's important that we don't set the title in the call
        # above, because we don't want to have the id chosen based on
        # the title.
        folder.title = data['title']
        folder.description = data.get('description')
        folder.language = lang_id

        # It's a navigation root!
        alsoProvides(folder, INavigationRoot)

        # Exclude folder from navigation (if applicable)
        adapter = IExcludeFromNavigation(folder, None)
        if adapter is not None:
            adapter.exclude_from_nav = True

        # We've modified the object; reindex.
        notify(modified(folder))

        IStatusMessage(self.request).addStatusMessage(
            _(u"${fti_name} created.", mapping={
                'fti_name': translate(fti.Title(), context=self.request)
            }), "info")

        self.request.response.redirect(data['next_url'])


class SetTranslationForView(Form):
    label = _(u"Select translation")
    description = _(
        u"Locate an existing content item for which the current item "
        u"is a translation. If the selected item already has been "
        u"translated into the current language, the other reference "
        u"will be removed."
    )

    fields = field.Fields(ISelectTranslation)
    ignoreContext = True

    def getContent(self):
        return getToolByName(self.context, 'portal_url').getPortalObject()

    @button.buttonAndHandler(_(u'Use'))
    def handleUse(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = _("Please correct errors.")
            return

        obj = data['target']
        lt = getToolByName(self.context, 'portal_languages')

        default_lang = lt.getDefaultLanguage()

        language = aq_base(self.context).language or default_lang
        obj_lang = aq_base(obj).language or default_lang

        if language == obj_lang:
            lang_name = self.request.locale.displayNames.languages.get(
                obj_lang,
                _(u"n/a")
            )

            self.status = _(
                u"The referenced content item is set to the "
                u"same language: ${lang}.", mapping={'lang': lang_name})

            return

        # Check if an existing translation in the current language
        # already exists.
        translations = ITranslationGraph(obj).getTranslations()
        for lang_id, item in translations:
            if lang_id or default_lang != language:
                continue

            parent = ITranslationGraph(item).detach()
            if parent is not None:
                title = item.Title().decode('utf-8')
                IStatusMessage(self.request).addStatusMessage(
                    _(u"The existing reference to \"${title}\" has "
                      u"been replaced.", mapping={'title': title}),
                    "info"
                )

                modified(parent)

        # Register new translation.
        ITranslationGraph(self.context).registerTranslation(obj)
        modified(obj)

        IStatusMessage(self.request).addStatusMessage(
            _(u"Translation registered."), "info"
        )

        next_url = self.context.absolute_url()
        self.request.response.redirect(next_url)


class ClearTranslationsView(Form):
    label = _(u"Clear translations")
    description = _(
        u"Please confirm that you want to clear the translation "
        u"references."
    )

    fields = field.Fields(IClearTranslations)

    @button.buttonAndHandler(_(u'Clear'))
    def handleClear(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = _("Please correct errors.")
            return

        graph = ITranslationGraph(self.context)
        graph.clear()
        parent = graph.detach()
        if parent is not None:
            modified(parent)

        IStatusMessage(self.request).addStatusMessage(
            _(u"References cleared."), "info"
        )

        next_url = self.context.absolute_url()
        self.request.response.redirect(next_url)
