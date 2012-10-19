This add-on provides support for content in multiple languages
(multilingual). It's compatible with Plone 4.2 or better with
`Dexterity <http://plone.org/products/dexterity>`_ content only.

Skip to `history`_ to learn about other add-ons that provide a similar
functionality.

Found a bug? Please use the `issue tracker
<https://github.com/collective/collective.multilingual/issues>`_.

.. image:: https://secure.travis-ci.org/collective/collective.multilingual.png
    :target: http://travis-ci.org/collective/collective.multilingual


Usage
=====

To make a content type multilingual-aware, enable the "Multilingual"
behavior using the control panel.

The primary interaction is through a new *translate* menu which is
available for content items for which the behavior is enabled.

.. note:: Plone only includes the default language in the list of
          supported languages. Visit the *language tool* in the ZMI to
          add more languages to the list.

The translate menu lists each of the supported languages and links to
either the default view (if already translated), or an add form.

If a language folder (see below) does not exist for the chosen
language, the user will first be prompted to create one, using the
"Setup language folder" form. In most cases, the user can click
straight through to the add form: sensible form defaults are provided.


Plone in multiple languages
===========================

Out of the box, Plone supports a language setup where language in the
default language lives in the root:

    ``/`` ⇐ *default content*

This is also the root for language-neutral content. For other
languages, content in this setup lives in:

    ``/<language-id>/`` ⇐ *content in other language*

The *language id* is the `two-letter country code
<http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_. For instance, for
Denmark this is ``"da"``.

We'll call these *language folders*. Plone can be set up to
automatically change the language of the entire user interface to that
of the language folder when the user visits a page contained below it.

Setting up a language folder
----------------------------

You can either set up language folders manually, or use the "Setup
language folder" form which is shown when you try to add a translation
for a content in a language for which a language folder does not
exist.

In both cases, you can use any content type which is a "container" (it
can contain other items). This is typically a folder. The most common
container type will be suggested by the "Setup language folder" form.

Note that a language folder is a navigation root. The
``INavigationRoot`` interface is automatically added as a marker
interface to signal this to Plone's user interface. In practical
terms, this means for instance that the navigation portlet will use
the language folder as the "root" content item.


Translation of default pages
----------------------------

In Plone, a default page can be selected for a container in which case
the page is shown instead of the container as the *default view*.

Since Plone's user interface shows a single interface for the
composition of a container and a default page, we require that the
container is translated before the default page.


The translation relationship
----------------------------

The data structure that records the translation relationship between
content is a `directed acyclic graph
<http://en.wikipedia.org/wiki/Directed_acyclic_graph>`_:

    Every vertex is a content item, and edges are a translation from one
    language to another. For example, original content in English might
    first be translated into German, and then from this translation, into
    French. This would be a graph with three vertices and two edges.

In the content model, this is implemented as the ``translations`` set
relation where the UUID (universally unique identifier) is used as the
content item reference value.

Plone comes with a behavior that adds a language setting to content
items, and this behavior must be enabled in order to translate
content.


API
===

The interface ``ITranslationGraph`` provides a view into the
translation graph for a context that provides the ``IMultilingual``
interface (implemented by the "Multilingual" behavior).

For each content object (this will be referred to in the following as
the ``context``) We can turn the graph into a mapping from language
ids to content objects, each of which is the ``context`` in some
translation:

>>> graph = ITranslationGraph(context)
>>> translations = graph.getTranslations()

The ``translations`` returned are a list of ``(language_id, content)``
which we can pass to the ``dict`` constructor to turn it into a
mapping object. Note that ``context`` is omitted.

>>> mapping = dict(translations)

For some applications, we want to establish a relation for each of the
supported languages to allow a user or visitor to get to the *nearest*
content object appearing in a supported language of choice. In this
situation, nearest will be defined as the closest ancestor
translation:

>>> nearest = graph.getNearestTranslations()

The ``nearest`` mapping is used to generate the "Translate" menu that
let's a contributor or editor navigate between the different
translations of a content object.

It's also used in the language selection viewlet which appears in
Plone when cookie-based language selection is enabled (see the
language tool for more information).


History
=======

In 2004, Jarn (formerly Plone Solutions) released `LinguaPlone
<http://pypi.python.org/pypi/Products.LinguaPlone>`_ which, although
still compatible with recent Plone releases, is now in legacy
status. It's recommended that you use this package if you have
`Archetypes <http://plone.org/products/archetypes>`_ content only.

In 2005, Ramon Navarro Bosch <r.navarro@iskra.cat> organized a sprint
in Girona on the subject of multilingual content in Plone. The idea
was to take advantage of the component architecture
(i.e. ``zope.interface`` and ``zope.component``) from the `Zope
Toolkit <http://docs.zope.org/zopetoolkit/>`_ to model an architecture
that could realistically support the diverse requirements for
multilingual content. The implementation of this architecture has been
an on-going process, but as of this writing, beta releases are
available for testing. The `plone.app.multilingual
<http://pypi.python.org/pypi/plone.app.multilingual>`_ (or PAM) pulls
in the required dependencies.

Note that PAM supports both Archetypes and Dexterity content. It also
tries to provide the user experience from LinguaPlone so that users
familiar with this add-on from previous versions of Plone will quickly
be able to use it.


Frequently Asked Questions
==========================

How does *collective.multilingual* compare to *plone.multilingual*?

  This add-on is a brand new implementation. It's an *alternative* to
  the existing solutions.

  The most important difference is that ``collective.multilingual`` is
  built for Plone 4. It fully benefits from the new features included
  in this release.

  The newer platform arguably makes the implementation simple, and
  this is not just a good thing, it also makes it much easier to
  maintain the software as a community.

  There's another key difference: *less features*. There is no compare
  view, and no integration with external translation tools. It's not
  that we don't want to be "feature complete", but some of these
  features are already provided by the web browser and it's not
  necessarily a good thing to try and implement these in Plone.

  In short, if you're *not* using the Archetypes content type
  framework (and you really shouldn't be, if you have a choice), then
  ``collective.multilingual`` is probably going to work well.

What's a *canonical item*?

  This is an item that you have created using Plone's *add* menu and
  which has been translated into one or more languages.

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

  There's a setting in Plone which decides whether this is unset
  (neutral), or set to the language which is currently the default.

  If content is created using the translate menu, then the language
  form default will be provided automatically.


