# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from kitconcept.contentcreator.testing import CONTENTCREATOR_CORE_INTEGRATION_TESTING  # noqa
from plone import api

try:
    from Products.CMFPlone.utils import get_installer
except ImportError:  # Plone < 5.1
    HAS_INSTALLER = False
else:
    HAS_INSTALLER = True

import unittest


class TestSetup(unittest.TestCase):
    """Test that kitconcept.contentcreator is properly installed."""

    layer = CONTENTCREATOR_CORE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        if HAS_INSTALLER:
            self.installer = get_installer(self.portal)
        else:
            self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if kitconcept.contentcreator is installed."""
        if HAS_INSTALLER:
            self.assertTrue(
                self.installer.is_product_installed('kitconcept.contentcreator')
            )
        else:
            self.assertTrue(
                self.installer.isProductInstalled(
                    'kitconcept.contentcreator'
                )
            )

    def test_browserlayer(self):
        """Test that IContentcreatorCoreLayer is registered."""
        from kitconcept.contentcreator.interfaces import (
            IContentcreatorCoreLayer)
        from plone.browserlayer import utils
        self.assertIn(IContentcreatorCoreLayer, utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = CONTENTCREATOR_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        if HAS_INSTALLER:
            self.installer = get_installer(self.portal)
            self.installer.uninstall_product('kitconcept.contentcreator')
        else:
            self.installer = api.portal.get_tool('portal_quickinstaller')
            self.installer.uninstallProducts(['kitconcept.contentcreator'])

    def test_product_uninstalled(self):
        """Test if kitconcept.contentcreator is cleanly uninstalled."""
        if HAS_INSTALLER:
            self.assertFalse(
                self.installer.is_product_installed('kitconcept.contentcreator')
            )
        else:
            self.assertFalse(
                self.installer.isProductInstalled(
                    'kitconcept.contentcreator'
                )
            )

    def test_browserlayer_removed(self):
        """Test that IContentcreatorCoreLayer is removed."""
        from kitconcept.contentcreator.interfaces import IContentcreatorCoreLayer
        from plone.browserlayer import utils
        self.assertNotIn(IContentcreatorCoreLayer, utils.registered_layers())
