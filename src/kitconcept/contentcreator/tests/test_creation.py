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

    def test_blocks_fields(self):
        content_structure = load_json("fields_blocks.json", __file__)

        applyProfile(self.portal, "plone.restapi:blocks")

        with api.env.adopt_roles(["Manager"]):
            create_item_runner(
                self.portal,
                content_structure,
                default_lang="en",
                default_wf_state="published",
            )
        self.assertIn("a-test-page", self.portal.objectIds())
        self.assertTrue(
            self.portal["a-test-page"].blocks["de4dcc60-aead-4188-a352-78a2e5c6adf8"][
                "text"
            ]["blocks"][0]["text"]
            == "HELLOOOOO"
        )  # noqa

    def test_default_blocks_fields(self):
        content_structure = load_json("fields_blocks.json", __file__)

        applyProfile(self.portal, "plone.restapi:blocks")

        with api.env.adopt_roles(["Manager"]):
            create_item_runner(
                self.portal,
                content_structure,
                default_lang="en",
                default_wf_state="published",
            )
        self.assertIn("a-test-page-with-default-blocks", self.portal.objectIds())
        self.assertEqual(
            2, len(self.portal["a-test-page-with-default-blocks"].blocks.items())
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

        self.assertIn("news-item-image", self.portal.objectIds())
        self.assertTrue(self.portal["news-item-image"].image)

    def test_file_fields(self):
        content_structure = load_json("fields_file.json", __file__)

        with api.env.adopt_roles(["Manager"]):
            create_item_runner(
                self.portal,
                content_structure,
                default_lang="en",
                default_wf_state="published",
                base_image_path=os.path.dirname(__file__),
            )
        self.assertIn("an-file", self.portal.objectIds())
        self.assertTrue(self.portal["an-file"].file)

        self.assertIn("another-file", self.portal.objectIds())
        self.assertTrue(self.portal["another-file"].file)

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

    def test_file_fields_deprecated(self):
        content_structure = load_json("fields_file.json", __file__)

        with api.env.adopt_roles(["Manager"]):
            create_item_runner(
                self.portal,
                content_structure,
                default_lang="en",
                default_wf_state="published",
                base_image_path=os.path.dirname(__file__),
            )
        self.assertIn("an-file-deprecated", self.portal.objectIds())
        self.assertTrue(self.portal["an-file-deprecated"].file)

        self.assertIn("another-file-deprecated", self.portal.objectIds())
        self.assertTrue(self.portal["another-file-deprecated"].file)

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

        self.assertEqual(self.portal["a-folder"].description, "The description")
