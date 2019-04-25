# -*- coding: utf-8 -*-
from kitconcept.contentcreator.interfaces import ICreateTestContent
from kitconcept.contentcreator.testing import CONTENTCREATOR_CORE_INTEGRATION_TESTING
from plone import api
from Products.CMFPlone.interfaces import IPloneSiteRoot
from zope.component import adapter
from zope.component import getAdapters
from zope.component import getGlobalSiteManager
from zope.interface import implementer

import unittest


@implementer(ICreateTestContent)
@adapter(IPloneSiteRoot)
class CreateNewsItemContent(object):
    """Example adapter to create initial content."""

    def __init__(self, context):
        self.context = context

    def __call__(self):
        api.content.create(
            container=self.context, type="News Item", title="Lorem Ipsum", id="newsitem"
        )


@implementer(ICreateTestContent)
@adapter(IPloneSiteRoot)
class CreatePageContent(object):
    """Example adapter to create initial content."""

    def __init__(self, context):
        self.context = context

    def __call__(self):
        api.content.create(
            container=self.context, type="Document", title="Lorem Ipsum", id="page"
        )


class AdaptersTestCase(unittest.TestCase):

    layer = CONTENTCREATOR_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        gsm = getGlobalSiteManager()
        gsm.registerAdapter(CreateNewsItemContent, name="newsitem")
        gsm.registerAdapter(CreatePageContent, name="page")

    def test_adapter(self):
        self.assertNotIn("newsitem", self.portal)
        self.assertNotIn("page", self.portal)
        with api.env.adopt_roles(["Manager"]):
            for name, provider in getAdapters((api.portal.get(),), ICreateTestContent):
                provider()
        self.assertIn("newsitem", self.portal)
        self.assertIn("page", self.portal)
