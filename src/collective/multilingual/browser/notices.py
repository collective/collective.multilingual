from zope.component import getMultiAdapter
from z3c.form.interfaces import IAddForm
from plone.z3cform.interfaces import IFormWrapper
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot

from ..interfaces import ITranslationGraph
from ..utils import getObjectByuuid


class NoticeViewletBase(object):
    available = False

    def render(self):
        if self.available:
            return self.index()

        return u""


class SupportedLanguagesNoticeViewlet(NoticeViewletBase):
    def update(self):
        lt = getToolByName(self.context, 'portal_languages')
        supported = lt.listSupportedLanguages()
        self.available = len(supported) <= 1


class ParentNotTranslatedNoticeViewlet(NoticeViewletBase):
    def update(self):
        form = self.__parent__

        if IFormWrapper.providedBy(form):
            form = form.form_instance

        if not IAddForm.providedBy(form):
            return

        uuid = self.request.form.get('translation')
        language = self.request.form.get('language')
        if not uuid or not language:
            return

        obj = getObjectByuuid(self.context, uuid)

        context_state = getMultiAdapter(
            (obj, self.request), name=u"plone_context_state"
            )

        # This is now the parent of the item that we're trying to
        # create a new translation for!
        obj = context_state.parent()

        # If it's the site root, then we're done.
        if IPloneSiteRoot.providedBy(obj):
            return

        # Now we just need to check if the parent has already been
        # translated into the required language in which case we're
        # also done.
        translations = ITranslationGraph(obj).getTranslations()
        if language in dict(translations):
            return

        # Okay, we'll show the notice.
        self.available = True
        self.folder = obj
        self.language = self.request.locale.displayNames.languages.\
                        get(language)
