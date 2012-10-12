This add-on provides support for content in multiple languages
(multilingual).

Compatibility: Plone 4.2+ with Dexterity


Overview
========

To make a content type multilingual-aware, enable the "Multilingual"
behavior using the control panel.

The primary interaction is through a new *translate* menu which is
available on content for which the behavior is enabled.

.. note:: Plone only includes the default language in the list of
          supported languages. Visit the *language tool* in the ZMI to
          add more languages to the list.

The translate menu shows an entry for each supported language and
either links to an add- or edit form.


Understanding language folders
------------------------------

Language in translation is created under ``/<language-id>``:

  While content in the default language (or "neutral" when unset)
  always lives at the site root ``/``, content in other languages live
  under ``/<language-id>``. For example::

    /front-page
    /da/forside
    /de/titelseite
    /fr/premiere-page

If an action is selected to select content into a language for which a
language folder has not yet been created, the user is first prompted
to create one.


The translation graph
---------------------

The data structure that records the translation relationship between
content is a `directed acyclic graph
<http://en.wikipedia.org/wiki/Directed_acyclic_graph>`_ where every
vertice is a content item, and edges are a translation from one
language to another. For example, original content in English might
first be translated into German, and then from this translation, into
French. This would be a graph with three vertices and two edges.


API
---

The interface ``ITranslationGraph`` provides a view into the
translation graph for a context that provides the ``IMultilingual``
interface (implemented by the "Multilingual" behavior):

>>> graph = ITranslationGraph(context)
>>> translations = graph.getTranslations()

The translations returned are a list ``(language_id, content)`` of all
the content items appearing in the translation graph *except* the
adaptation context itself.

You can turn it into a dictionary to look up a translation in some
language.

>>> languages = dict(translations)
>>> item = language['de']


To-Do
-----

There are some features that are missing at this point:

- Integration with Plone's search user interface and collections.


History
=======

In 2004, Jarn (formerly Plone Solutions) released `LinguaPlone
<http://pypi.python.org/pypi/Products.LinguaPlone>`_ which, although
still compatible with recent Plone releases, is now in legacy status.

In 2005, Ramon Navarro Bosch <r.navarro@iskra.cat> organized a sprint
in Girona on the subject of multilingual content in Plone. The idea
was to take advantage of the component architecture
(i.e. ``zope.interface`` and ``zope.component``) from the `Zope
Toolkit <http://docs.zope.org/zopetoolkit/>`_ to model an architecture
that could realistically support the diverse requirements for
multilingual content. This eventually lead to the development of
several packages including `plone.app.multilingual
<http://pypi.python.org/pypi/plone.app.multilingual>`_ (also known
simply as PAM).

Note that ``collective.multilingual`` (this package) is an
*alternative* to ``plone.multilingual`` and its related packages.


Frequently Asked Questions
==========================

What's a *canonical item*?

  This is a content item for which at least one translation exists,
  but which is not itself a translation of a content item. In other
  words, this content was created using Plone's "add menu".

Must I set a language for my content?

  No. If you don't set the language field, the language is considered
  neutral. At any given time, this effectively means the site's
  default language.

Can I have language-independent fields?

  Yes. You can set a value of ``True`` for the tagged value
  ``"plone.autoform.languageindependent"`` or use the included utility
  function::

    from collective.multilingual.interfaces import setLanguageIndependent
    from plone.app.dexterity.behaviors.metadata import IDublinCore

    setLanguageIndependent(
      IDublinCore['contributors'],
      IDublinCore['creators'],
      IDublinCore['rights'],
      )

  This is not just an example. These fields are actually set as
  language-independent.

  Note that when a field is language-independent, changes are copied
  into all the content items in the corresponding translation graph.

What's the language of newly created content?

  This is set using the language field. However, the default value
  shown in the add form depends on the container. If the container has
  a language setting, this is used as the default value.


