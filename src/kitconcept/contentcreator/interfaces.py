# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IContentcreatorCoreLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class ICreateTestContent(Interface):
    """Adapter for test content creation."""

    def __call__(self):
        """Create the test content if available."""
