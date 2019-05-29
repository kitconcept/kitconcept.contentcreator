# -*- coding: utf-8 -*-
from kitconcept.contentcreator.creator import create_item_runner
from kitconcept.contentcreator.creator import load_json
from kitconcept.contentcreator.testing import (
    CONTENTCREATOR_CORE_INTEGRATION_TESTING,
)  # noqa
from plone import api
from plone.app.testing import applyProfile

import os
import unittest


class CreatorTestCase(unittest.TestCase):

    layer = CONTENTCREATOR_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]

    def test_tiles_fields(self):
        content_structure = load_json("fields_tiles.json", __file__)

        applyProfile(self.portal, "plone.restapi:tiles")

        with api.env.adopt_roles(["Manager"]):
            create_item_runner(
                self.portal,
                content_structure,
                default_lang="en",
                default_wf_state="published",
            )
        self.assertIn("a-test-page", self.portal.objectIds())
        self.assertTrue(
            self.portal["a-test-page"].tiles["de4dcc60-aead-4188-a352-78a2e5c6adf8"][
                "text"
            ]["blocks"][0]["text"]
            == "HELLOOOOO"
        )  # noqa

    def test_default_tiles_fields(self):
        content_structure = load_json("fields_tiles.json", __file__)

        applyProfile(self.portal, "plone.restapi:tiles")

        with api.env.adopt_roles(["Manager"]):
            create_item_runner(
                self.portal,
                content_structure,
                default_lang="en",
                default_wf_state="published",
            )
        self.assertIn("a-test-page-with-default-tiles", self.portal.objectIds())
        self.assertEqual(
            3, len(self.portal["a-test-page-with-default-tiles"].tiles.items())
        )  # noqa

    def test_image_fields(self):
        content_structure = load_json("fields_image.json", __file__)

        with api.env.adopt_roles(["Manager"]):
            create_item_runner(
                self.portal,
                content_structure,
                default_lang="en",
                default_wf_state="published",
                base_image_path=os.path.dirname(__file__),
            )
        self.assertIn("an-image", self.portal.objectIds())
        self.assertTrue(self.portal["an-image"].image)

        self.assertIn("another-image", self.portal.objectIds())
        self.assertTrue(self.portal["another-image"].image)

    def test_image_fields_deprecated(self):
        content_structure = load_json("fields_image.json", __file__)

        with api.env.adopt_roles(["Manager"]):
            create_item_runner(
                self.portal,
                content_structure,
                default_lang="en",
                default_wf_state="published",
                base_image_path=os.path.dirname(__file__),
            )
        self.assertIn("an-image-deprecated", self.portal.objectIds())
        self.assertTrue(self.portal["an-image-deprecated"].image)

        self.assertIn("another-image-deprecated", self.portal.objectIds())
        self.assertTrue(self.portal["another-image-deprecated"].image)

    def test_edit_if_content_already_exists(self):
        content_structure = load_json("test_content.json", __file__)

        self.portal.invokeFactory("Folder", "a-folder")
        self.assertIn("a-folder", self.portal.objectIds())

        with api.env.adopt_roles(["Manager"]):
            create_item_runner(
                self.portal,
                content_structure,
                default_lang="en",
                default_wf_state="published",
            )

        self.assertEquals(self.portal["a-folder"].description, "The description")
