# -*- coding: utf-8 -*-
from plone.app.testing import TEST_USER_ID
from zope.component import queryUtility
from zope.component import createObject
from plone.app.testing import setRoles
from plone.dexterity.interfaces import IDexterityFTI
from plone import api

from kitconcept.contentcreator.testing import CONTENTCREATOR_CORE_INTEGRATION_TESTING  # noqa
from kitconcept.contentcreator.interfaces import IHomepage

import unittest


class KontaktIntegrationTest(unittest.TestCase):

    layer = CONTENTCREATOR_CORE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.installer = api.portal.get_tool('portal_quickinstaller')
        fti = queryUtility(IDexterityFTI, name='Homepage')
        fti.global_allow = True

    def test_schema(self):
        fti = queryUtility(IDexterityFTI, name='Homepage')
        schema = fti.lookupSchema()
        self.assertEqual(IHomepage, schema)

    def test_fti(self):
        fti = queryUtility(IDexterityFTI, name='Homepage')
        self.assertTrue(fti)

    def test_factory(self):
        fti = queryUtility(IDexterityFTI, name='Homepage')
        factory = fti.factory
        obj = createObject(factory)
        self.assertTrue(IHomepage.providedBy(obj))

    def test_adding(self):
        self.portal.invokeFactory('Homepage', 'Homepage')
        self.assertTrue(
            IHomepage.providedBy(self.portal['Homepage'])
        )
