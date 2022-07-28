from DateTime import DateTime
from kitconcept import api
from kitconcept.contentcreator.creator import content_creator_from_folder
from kitconcept.contentcreator.creator import create_item_runner
from kitconcept.contentcreator.creator import load_json
from kitconcept.contentcreator.creator import refresh_objects_created_by_structure
from kitconcept.contentcreator.testing import CONTENTCREATOR_CORE_INTEGRATION_TESTING
from plone.app.multilingual.api import get_translation_manager
from plone.app.multilingual.browser.setup import SetupMultilingualSite
from plone.app.multilingual.setuphandlers import enable_translatable_behavior
from plone.app.testing import applyProfile
from Products.CMFCore.utils import getToolByName

import json
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
        self.assertTrue(self.portal["another-image"].image.filename, "image.png")
        self.assertTrue(self.portal["another-image"].image.contentType, "image/png")

        self.assertIn("image-svg", self.portal.objectIds())
        self.assertTrue(self.portal["image-svg"].image)
        self.assertTrue(self.portal["image-svg"].image.filename, "image.svg")
        self.assertTrue(self.portal["image-svg"].image.contentType, "image/svg")

        self.assertIn("news-item-image", self.portal.objectIds())
        self.assertTrue(self.portal["news-item-image"].image)
        self.assertTrue(self.portal["news-item-image"].image.filename, "image.png")
        self.assertTrue(self.portal["news-item-image"].image.contentType, "image/png")

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
        self.assertIn("a-file", self.portal.objectIds())
        self.assertTrue(self.portal["a-file"].file)

        self.assertIn("another-file", self.portal.objectIds())
        self.assertTrue(self.portal["another-file"].file)
        self.assertTrue(self.portal["another-file"].file.filename, "report.pdf")
        self.assertTrue(self.portal["another-file"].file.contentType, "application/pdf")

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
        self.assertTrue(
            self.portal["another-image-deprecated"].image.filename, "image.png"
        )
        self.assertTrue(
            self.portal["another-image-deprecated"].image.contentType, "image/png"
        )

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
        self.assertIn("a-file-deprecated", self.portal.objectIds())
        self.assertTrue(self.portal["a-file-deprecated"].file)

        self.assertIn("another-file-deprecated", self.portal.objectIds())
        self.assertTrue(self.portal["another-file-deprecated"].file)
        self.assertTrue(self.portal["another-file"].file.filename, "report.pdf")
        self.assertTrue(self.portal["another-file"].file.contentType, "application/pdf")

    def test_edit_if_content_already_exists(self):
        content_structure = load_json("test_content.json", __file__)

        self.portal.invokeFactory("Folder", "a-folder")
        self.assertIn("a-folder", self.portal.objectIds())
        self.portal.invokeFactory("Folder", "a-folder-with-no-id")
        self.assertIn("a-folder-with-no-id", self.portal.objectIds())

        with api.env.adopt_roles(["Manager"]):
            create_item_runner(
                self.portal,
                content_structure,
                default_lang="en",
                default_wf_state="published",
            )

        self.assertEqual(self.portal["a-folder"].description, "The description")
        self.assertEqual(
            self.portal["a-folder-with-no-id"].description, "The description edited"
        )

    def test_content_from_folder(self):
        path = os.path.join(os.path.dirname(__file__), "content")

        with api.env.adopt_roles(["Manager"]):
            content_creator_from_folder(folder_name=path)

        self.assertEqual(["front-page", "a-folder"], self.portal.contentIds())
        self.assertEqual(
            [
                "a-document-1",
                "a-document-2",
                "a-document-3",
                "a-link",
                "the-last-document",
            ],
            self.portal["a-folder"].contentIds(),
        )

    def test_content_from_folder_indexing(self):
        content = os.path.join(os.path.dirname(__file__), "content")
        edited_content = os.path.join(os.path.dirname(__file__), "alternate")

        with api.env.adopt_roles(["Manager"]):
            content_creator_from_folder(folder_name=content)

        results = api.content.find(Title="Test Document 1")
        self.assertEqual(1, len(results))

        with api.env.adopt_roles(["Manager"]):
            content_creator_from_folder(folder_name=edited_content)

        results = api.content.find(Title="Test Document Edited Title")
        self.assertEqual(1, len(results))
        results = api.content.find(Title="Test Document 1")
        self.assertEqual(0, len(results))

        # Also works for SearchableText (content inside a Slate block)
        results = api.content.find(SearchableText="this is a slate link inside")
        self.assertEqual(1, len(results))

    def test_content_from_folder_with_excludes(self):
        path = os.path.join(os.path.dirname(__file__), "content")

        with api.env.adopt_roles(["Manager"]):
            content_creator_from_folder(
                folder_name=path, exclude=["a-folder.a-document-1"]
            )

        self.assertEqual(["front-page", "a-folder"], self.portal.contentIds())
        self.assertEqual(
            ["a-document-2", "a-document-3", "a-link", "the-last-document"],
            self.portal["a-folder"].contentIds(),
        )

    def test_content_from_folder_custom_order(self):
        path = os.path.join(os.path.dirname(__file__), "content")

        with api.env.adopt_roles(["Manager"]):
            content_creator_from_folder(
                folder_name=path,
                custom_order=[
                    "a-folder.a-document-2.json",
                    "a-folder.a-document-1.json",
                ],
            )

        self.assertEqual(["front-page", "a-folder"], self.portal.contentIds())
        self.assertEqual(
            [
                "a-document-2",
                "a-document-1",
                "a-document-3",
                "a-link",
                "the-last-document",
            ],
            self.portal["a-folder"].contentIds(),
        )

    def test_content_from_folder_types_order(self):
        path = os.path.join(os.path.dirname(__file__), "content")

        with api.env.adopt_roles(["Manager"]):
            content_creator_from_folder(
                folder_name=path,
                types_order=["Link", "Document"],
            )

        self.assertEqual(
            [
                "a-link",
                "a-document-1",
                "a-document-2",
                "a-document-3",
                "the-last-document",
            ],
            self.portal["a-folder"].contentIds(),
        )

    def test_content_from_folder_siteroot(self):
        path = os.path.join(os.path.dirname(__file__), "content")
        blocks = {
            "d3f1c443-583f-4e8e-a682-3bf25752a300": {"@type": "title"},
            "7624cf59-05d0-4055-8f55-5fd6597d84b0": {"@type": "text"},
        }
        blocks_layout = {
            "items": [
                "d3f1c443-583f-4e8e-a682-3bf25752a300",
                "7624cf59-05d0-4055-8f55-5fd6597d84b0",
            ]
        }
        with api.env.adopt_roles(["Manager"]):
            content_creator_from_folder(folder_name=path)

        self.assertEqual(blocks, json.loads(self.portal.blocks))
        self.assertEqual(blocks_layout, json.loads(self.portal.blocks_layout))

    def test_repeat_creation_twice(self):
        path = os.path.join(os.path.dirname(__file__), "content")
        blocks = {
            "d3f1c443-583f-4e8e-a682-3bf25752a300": {"@type": "title"},
            "7624cf59-05d0-4055-8f55-5fd6597d84b0": {"@type": "text"},
        }
        blocks_layout = {
            "items": [
                "d3f1c443-583f-4e8e-a682-3bf25752a300",
                "7624cf59-05d0-4055-8f55-5fd6597d84b0",
            ]
        }
        with api.env.adopt_roles(["Manager"]):
            content_creator_from_folder(folder_name=path)

        self.assertEqual(blocks, json.loads(self.portal.blocks))
        self.assertEqual(blocks_layout, json.loads(self.portal.blocks_layout))

        self.portal["a-folder"]["a-document-1"].title = "the modified title"

        with api.env.adopt_roles(["Manager"]):
            content_creator_from_folder(folder_name=path)

        self.assertEqual(
            self.portal["a-folder"]["a-document-1"].title, "Test Document 1"
        )

    # def test_get_contents(self):
    #     path = os.path.join(os.path.dirname(__file__), "content_with_refresh")
    #     with api.env.adopt_roles(["Manager"]):
    #         content_creator_from_folder(folder_name=path)

    #     content_structure = load_json(
    #         os.path.join(os.path.dirname(__file__), "content", "content.json")
    #     )

    #     result = get_objects_created(api.portal.get(), content_structure)

    #     pass

    def test_refresh_objects_created_by_structure(self):
        path = os.path.join(os.path.dirname(__file__), "content_with_refresh")
        with api.env.adopt_roles(["Manager"]):
            content_creator_from_folder(folder_name=path)

        content_structure = load_json(
            os.path.join(
                os.path.dirname(__file__), "content_with_refresh", "content.json"
            )
        )

        refresh_objects_created_by_structure(api.portal.get(), content_structure)
        self.assertTrue(
            "resolveuid" in json.dumps(self.portal["a-folder"]["a-document"].blocks)
        )

        pass

    def test_edit_if_content_already_exists_given_modified_date(self):
        content_structure = load_json("test_content.json", __file__)

        self.portal.invokeFactory("Folder", "a-folder")
        self.assertIn("a-folder", self.portal.objectIds())

        with api.env.adopt_roles(["Manager"]):
            create_item_runner(
                self.portal,
                content_structure,
                default_lang="en",
                default_wf_state="published",
                do_not_edit_if_modified_after="2021-07-12",
            )

        self.assertEqual(self.portal["a-folder"].description, "")

    def test_effective_date_is_set_if_review_state_published(self):
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

        self.assertTrue(self.portal["a-folder"].effective() < DateTime())

    def test_content_from_folder_with_translations(self):
        # install plone.app.multilingual
        language_tool = getToolByName(self.portal, "portal_languages")
        language_tool.addSupportedLanguage("de")
        language_tool.addSupportedLanguage("en")
        sms = SetupMultilingualSite(self.portal)
        sms.setupSite(self.portal)
        enable_translatable_behavior(self.portal)

        path = os.path.join(os.path.dirname(__file__), "content_with_translations")
        with api.env.adopt_roles(["Manager"]):
            content_creator_from_folder(folder_name=path)

        de = self.portal["de"]["seite"]
        self.assertEqual(de.language, "de")
        en = self.portal["en"]["page"]
        self.assertEqual(en.language, "en")
        self.assertEqual(get_translation_manager(en).tg, get_translation_manager(de).tg)
