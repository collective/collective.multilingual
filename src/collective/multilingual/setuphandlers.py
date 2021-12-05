from zope.interface import implementer


try:
    from Products.CMFPlone.interfaces import INonInstallable
except ImportError:
    from zope.interface import Interface

    class INonInstallable(Interface):
        pass


@implementer(INonInstallable)
class HiddenProfiles(object):
    def getNonInstallableProfiles(self):
        """Hide all profiles from site-creation and quickinstaller."""
        return [
            "collective.multilingual:default",
            "collective.multilingual:uninstall",
        ]

    def getNonInstallableProducts(self):
        """Hide the upgrades package from site-creation and quickinstaller.

        Our upgrades profiles are defined in the directory 'upgrades'.
        Plone sees this is a separate product.
        So instead of adding each new upgrade profile to the list of
        non installable profiles above, we can mark the upgrades product
        as non installable.
        """
        return ["collective.multilingual.upgrades"]
