.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide.html
   This text does not appear on pypi or github. It is a comment.

==============================================================================
kitconcept.contentcreator
==============================================================================

.. image:: https://kitconcept.com/logo.svg
   :alt: kitconcept
   :target: https://kitconcept.com/


.. image:: https://github.com/kitconcept/kitconcept.contentcreator/workflows/kitconcept.contentcreator%20CI/badge.svg
    :target: https://github.com/kitconcept/kitconcept.contentcreator/actions?query=workflow%3A%22kitconcept.contentcreator+CI%22

This package is the responsible for automated content creation via
plone.restapi serializers/creators.

Initially based on ``collective.contentcreator`` written by Johannes Raggam (@thet) and evolved and improved from it.

Usage
=====

Basic
-----

It allows to have a structure in your policy package like::

  |-content_creator
      |- content.json
      |- siteroot.json
      |- de.mysection.json
      |- ...
      |- images
  |-content_images

using these names (for both files and folders) as sensible defaults. This is the
recommended way, although you can specify runners for custom JSON files (see below).

and creates the content in a tree like from `content.json` using the runner, and
object by object using the standalone json files.

The ``images`` folder is blacklisted to support the images folder to be inside the creator folder.

In your setuphandlers.py you need to::

  from kitconcept.contentcreator.creator import content_creator_from_folder
  ...

  content_creator_from_folder()

the method ``content_creator_from_folder`` has the following signature::

  def content_creator_from_folder(
    folder_name=os.path.join(os.path.dirname(__file__), "content_creator"),
    base_image_path=os.path.join(os.path.dirname(__file__), "content_images"),
    default_lang=None,
    default_wf_state=None,
    ignore_wf_types=["Image", "File"],
    logger=logger,
    temp_enable_content_types=[],
    custom_order=[],
  ):

Creator runner given a single file
----------------------------------

Given a JSON file containing an array of objects to be created, this runner takes this
array content (should have plone.restapi syntax compliant structure) and creates content
out of it. You can load it using the method: ``load_json``::

  from kitconcept.contentcreator.creator import load_json

  content_structure = load_json('testcontent/content.json', __file__)

Then you can call the runner with the method ``create_item_runner``::

  from kitconcept.contentcreator.creator import create_item_runner

  create_item_runner(
      api.portal.get(),
      content_structure,
      default_lang='en',
      default_wf_state='published'
  )

Creator runner given a folder with multiple files
-------------------------------------------------

Each file should contain a single p.restapi JSON compliant object (non arrayed, can't
contain other objects). It takes the placement in the tree hierarchy and the object id
from the filename name (eg. de.beispiele.bildergroessen.json)

Setup runners from external modules/packages
--------------------------------------------

Alternativelly, you can create custom content creators in other packages and
call them all at the same time, via a custom adapter::

  from kitconcept.contentcreator.interfaces import ICreateTestContent

  for name, provider in getAdapters((api.portal.get(), ), ICreateTestContent):
    provider()

this should be the declaration in the other package::

  @implementer(ICreateTestContent)
  @adapter(IPloneSiteRoot)
  class CreatePFGContent(object):
      """Adapter to create PFG initial content."""

      def __init__(self, context):
          self.context = context

      def __call__(self):
          content_structure = load_json('testcontent/content.json', __file__)

          create_item_runner(
              api.portal.get(),
              content_structure,
              default_lang='en',
              default_wf_state='published',
              ignore_wf_types=[
                  'FormBooleanField',
                  'FormDateField',
                  'FormFileField',
                  'FormFixedPointField',
                  'FormIntegerField',
                  'FormLabelField',
                  'FormLinesField',
                  'FormPasswordField',
              ],
          )

other common use is calling from a folder::

  from kitconcept.contentcreator.creator import content_creator_from_folder

  content_creator_from_folder(
      folder_name=os.path.join(os.path.dirname(__file__), "content_creator"),
      base_image_path=os.path.join(os.path.dirname(__file__), "images"),
      default_lang='en',
      default_wf_state='published',
      ignore_wf_types=[
          'FormBooleanField',
          'FormDateField',
          'FormFileField',
          'FormFixedPointField',
          'FormIntegerField',
          'FormLabelField',
          'FormLinesField',
          'FormPasswordField',
      ],
      logger=logger,
      temp_enable_content_types=[],
      custom_order=[
        'object-id-2.json',
        'object-id-3.json',
        'object-id-1.json',
      ],
  )

Images and Files
----------------

For the creation of images, you can use the plone.restapi approach using the
following serialization mapping containg the file data and some additional
metadata:

- ``data`` - the base64 encoded contents of the file
- ``encoding`` - the encoding you used to encode the data, so usually `base64`
- ``content-type`` - the MIME type of the file
- ``filename`` - the name of the file, including extension

.. code-block:: json

      {
        "...": "",
        "@type": "File",
        "title": "My file",
        "file": {
            "data": "TG9yZW0gSXBzdW0uCg==",
            "encoding": "base64",
            "filename": "lorem.txt",
            "content-type": "text/plain"}
      }

Alternativelly, you can provide the image an extra property ``set_dummy_image``
with an array of (image) field names that will create a dummy image placeholder
in the specified fields in the to be created content type::

      {
        "id": "an-image",
        "@type": "Image",
        "title": "Test Image",
        "set_dummy_image": ["image"]
      }

A deprecated syntax form is also supported (it will create the image in the
``image`` field)::

      {
        "id": "an-image",
        "@type": "Image",
        "title": "Test Image",
        "set_dummy_image": true
      }

You can specify a real image too, using a dict in the ``set_local_image`` JSON
attribute with the field name and the filename of the real image::

      {
        "id": "another-image",
        "@type": "Image",
        "title": "Another Test Image",
        "set_local_image": {"image": "image.png"}
      }

Again, a deprecated form is also supported (it will create the image in the
``image`` field)::

      {
        "id": "another-image",
        "@type": "Image",
        "title": "Another Test Image",
        "set_local_image": "image.png"
      }

the same syntax is valid for files::

      {
        "id": "an-file",
        "@type": "File",
        "title": "Test File",
        "set_dummy_file": ["file"]
      }

the deprecated form is also supported (it will create the file in the
``file`` field)::

      {
        "id": "an-file",
        "@type": "File",
        "title": "Test File",
        "set_dummy_file": true
      }

You can specify a real file too, using a dict in the ``set_local_file`` JSON
attribute with the field name and the filename of the real file::

      {
        "id": "another-file",
        "@type": "File",
        "title": "Another Test File",
        "set_local_file": {"file": "file.png"}
      }

the deprecated form is also supported (it will create the file in the
``file`` field)::

      {
        "id": "another-file",
        "@type": "File",
        "title": "Another Test File",
        "set_local_file": "file.png"
      }

For all local images and files specified, you can specify the ``base_path`` for the image in the ``create_item_runner``::

  create_item_runner(
      api.portal.get(),
      content_structure,
      default_lang='en',
      default_wf_state='published',
      base_image_path=__file__
  )


Development
-----------

Requirements:

- Python 3
- venv

Setup::

  make

Run Static Code Analysis::

  make code-Analysis

Run Unit / Integration Tests::

  make test

Run Robot Framework based acceptance tests::

  make test-acceptance
