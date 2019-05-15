# -*- coding: utf-8 -*-
from kitconcept.contentcreator.creator import create_item_runner
from kitconcept.contentcreator.creator import load_json
from kitconcept.contentcreator.testing import CONTENTCREATOR_CORE_INTEGRATION_TESTING  # noqa
from plone import api
from plone.app.testing import applyProfile
from plone.restapi.behaviors import ITiles

import unittest


class CreatorTestCase(unittest.TestCase):

    layer = CONTENTCREATOR_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]

    def test_tiles_fields(self):
        content_structure = load_json("fields_tiles.json", __file__)

        applyProfile(self.portal, 'plone.restapi:tiles')

        with api.env.adopt_roles(["Manager"]):
            create_item_runner(
                self.portal,
                content_structure,
                default_lang="en",
                default_wf_state="published",
            )
        self.assertIn('a-test-page', self.portal.objectIds())
        self.assertTrue(self.portal['a-test-page'].tiles['de4dcc60-aead-4188-a352-78a2e5c6adf8']['text']['blocks'][0]['text'] == 'HELLOOOOO') # noqa
        self.assertTrue(ITiles.providedBy(self.portal['a-test-page']))

    def test_image_fields(self):
        content_structure = load_json("fields_image.json", __file__)

        with api.env.adopt_roles(["Manager"]):
            create_item_runner(
                self.portal,
                content_structure,
                default_lang="en",
                default_wf_state="published",
                base_image_path=__file__
            )
        self.assertIn('an-image', self.portal.objectIds())
        self.assertTrue(self.portal['an-image'].image)

        self.assertIn('another-image', self.portal.objectIds())
        self.assertTrue(self.portal['another-image'].image)
