Changes
=======

2.0 (unreleased)
----------------

- Fall back to English language names when the localized list offered
  by Zope does not provide one.
  [malthe]

- Plone 5.2 and Python 3 support.
  [thet]

- Language switcher: Do not render a link for the current language.
  [thet]


1.0.1 (2016-03-30)
------------------

- Fix issue where a widget that was updated multiple times would
  result in a circular translation reference.
  [malthe]

- Fix issue where translating _into_ the default language would ignore translated parents
  and place the new translation in the site root.
  [tmog]

- Always show "Clear..." and "This is a translation of..." menu items for context, even if context is a default page.
  [tmog]

- check to make sure we do not add multiple translations for one language. Even if one is neutral and the other is not.
  [tmog]

- Initial public release.
