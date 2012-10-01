from zope.interface import Interface
from z3c.form.interfaces import IWidget


class ILanguageIndependent(Interface):
    """Marker-interface for a language-independent component.

    For example, widgets that correspond to language-independent
    fields are set to provide this interface.
    """


class ILanguageIndependentWidget(ILanguageIndependent, IWidget):
    """Marker-interface for a language-independent widget."""
