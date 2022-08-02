<div align="center"><img alt="logo" src="https://kitconcept.com/logo.svg" width="150" /></div>

<h1 align="center">kitconcept.contentcreator</h1>

This package is the responsible for automated content creation via plone.restapi serializers/creators.

Initially based on `collective.contentcreator` written by Johannes Raggam (@thet) and evolved and improved from it.

<div align="center">

[![PyPI](https://img.shields.io/pypi/v/kitconcept.contentcreator)](https://pypi.org/project/kitconcept.contentcreator/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/kitconcept.contentcreator)](https://pypi.org/project/kitconcept.contentcreator/)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/kitconcept.contentcreator)](https://pypi.org/project/kitconcept.contentcreator/)
[![PyPI - License](https://img.shields.io/pypi/l/kitconcept.contentcreator)](https://pypi.org/project/kitconcept.contentcreator/)
[![PyPI - Status](https://img.shields.io/pypi/status/kitconcept.contentcreator)](https://pypi.org/project/kitconcept.contentcreator/)


[![PyPI - Plone Versions](https://img.shields.io/pypi/frameworkversions/plone/kitconcept.contentcreator)](https://pypi.org/project/kitconcept.contentcreator/)

[![Code analysis checks](https://github.com/kitconcept/kitconcept.contentcreator/actions/workflows/code-analysis.yml/badge.svg)](https://github.com/kitconcept/kitconcept.contentcreator/actions/workflows/code-analysis.yml)
[![Tests](https://github.com/kitconcept/kitconcept.contentcreator/actions/workflows/tests.yml/badge.svg)](https://github.com/kitconcept/kitconcept.contentcreator/actions/workflows/tests.yml)
![Code Style](https://img.shields.io/badge/Code%20Style-Black-000000)

[![GitHub contributors](https://img.shields.io/github/contributors/kitconcept/kitconcept.contentcreator)](https://github.com/kitconcept/kitconcept.contentcreator)
[![GitHub Repo stars](https://img.shields.io/github/stars/kitconcept/kitconcept.contentcreator?style=social)](https://github.com/kitconcept/kitconcept.contentcreator)

</div>


Usage
=====

Basic
-----

It allows to have a structure in your policy package like:

```
|-content_creator
    |- content.json
    |- siteroot.json
    |- de.mysection.json
    |- ...
    |- images
|-content_images
```

using these names (for both files and folders) as sensible defaults. This is the
recommended way, although you can specify runners for custom JSON files (see below).

and creates the content in a tree like from `content.json` using the runner, and
object by object using the standalone json files.

The {file}`images` folder is blacklisted to support the images folder to be inside the creator folder.

In your setuphandlers.py you need to:

```python
from kitconcept.contentcreator.creator import content_creator_from_folder

content_creator_from_folder()
```

the method `content_creator_from_folder` has the following signature:

```python
    def content_creator_from_folder(
        folder_name=os.path.join(os.path.dirname(__file__), "content_creator"),
        base_image_path=os.path.join(os.path.dirname(__file__), "content_images"),
        default_lang=None,
        default_wf_state=None,
        ignore_wf_types=["Image", "File"],
        logger=logger,
        temp_enable_content_types=[],
        custom_order=[],
        do_not_edit_if_modified_after=None,
        exclude=[],
    ):

```

The creator will bail out (raise) if any object errors on creation (or edition). There are
a couple of environment variables to control this behavior: `CREATOR_DEBUG` and
`CREATOR_CONTINUE_ON_ERROR`.

One can exclude elements (ids, without .json sufix) using the `exclude` kwargs.

You can control if the edit should happen or not for a given element providing the modified date
of the element is after the one specified in `do_not_edit_if_modified_after` kwargs.

Creator runner given a single file
----------------------------------

Given a JSON file containing an array of objects to be created, this runner takes this
array content (should have plone.restapi syntax compliant structure) and creates content
out of it. You can load it using the method: `load_json`:

```python
from kitconcept.contentcreator.creator import load_json

content_structure = load_json('testcontent/content.json', __file__)
```

Then you can call the runner with the method `create_item_runner`:

```python
from kitconcept.contentcreator.creator import create_item_runner

create_item_runner(
    api.portal.get(),
    content_structure,
    default_lang='en',
    default_wf_state='published'
)
```

Creator runner given a folder with multiple files
-------------------------------------------------

Each file should contain a single p.restapi JSON compliant object (non arrayed, can't
contain other objects). It takes the placement in the tree hierarchy and the object id
from the filename name (eg. de.beispiele.bildergroessen.json)

Setup runners from external modules/packages
--------------------------------------------

Alternativelly, you can create custom content creators in other packages and
call them all at the same time, via a custom adapter:

```python
from kitconcept.contentcreator.interfaces import ICreateTestContent

for name, provider in getAdapters((api.portal.get(), ), ICreateTestContent):
    provider()
```

this should be the declaration in the other package:

```python
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
```

other common use is calling from a folder:

```python
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
```

Images and Files
----------------

For the creation of images, you can use the plone.restapi approach using the
following serialization mapping containg the file data and some additional
metadata:

- **data** - the base64 encoded contents of the file
- **encoding** - the encoding you used to encode the data, so usually `base64`
- **content-type** - the MIME type of the file
- **filename** - the name of the file, including extension

```json
{
  "...": "",
  "@type": "File",
  "title": "My file",
  "file": {
    "data": "TG9yZW0gSXBzdW0uCg==",
    "encoding": "base64",
    "filename": "lorem.txt",
    "content-type": "text/plain"
  }
}
```

Alternatively, you can provide the image an extra property `set_dummy_image`
with an array of (image) field names that will create a dummy image placeholder
in the specified fields in the to be created content type:

```json
{
  "id": "an-image",
  "@type": "Image",
  "title": "Test Image",
  "set_dummy_image": ["image"]
}
```

A deprecated syntax form is also supported (it will create the image in the
`image` field)::

```json
{
  "id": "an-image",
  "@type": "Image",
  "title": "Test Image",
  "set_dummy_image": true
}
```

You can specify a real image too, using a dict in the `set_local_image` JSON
attribute with the field name and the filename of the real image:

```json
{
  "id": "another-image",
  "@type": "Image",
  "title": "Another Test Image",
  "set_local_image": {"image": "image.png"}
}
```

Again, a deprecated form is also supported (it will create the image in the
`image` field):

```json
{
  "id": "another-image",
  "@type": "Image",
  "title": "Another Test Image",
  "set_local_image": "image.png"
}
```


By default, image scales are generated immediately. To disable this,
set the `CREATOR_SKIP_SCALES` environment variable.

The same syntax is valid for files:

```json
{
  "id": "an-file",
  "@type": "File",
  "title": "Test File",
  "set_dummy_file": ["file"]
}
```

The deprecated form is also supported (it will create the file in the
`file` field):

```json
{
  "id": "an-file",
  "@type": "File",
  "title": "Test File",
  "set_dummy_file": true
}
```

You can specify a real file too, using a dict in the `set_local_file` JSON
attribute with the field name and the filename of the real file:

```json
{
  "id": "another-file",
  "@type": "File",
  "title": "Another Test File",
  "set_local_file": {"file": "file.png"}
}
```

the deprecated form is also supported (it will create the file in the
`file` field):

```json
{
  "id": "another-file",
  "@type": "File",
  "title": "Another Test File",
  "set_local_file": "file.png"
}
```

For all local images and files specified, you can specify the `base_path` for the image in the `create_item_runner`:

```python
create_item_runner(
    api.portal.get(),
    content_structure,
    default_lang='en',
    default_wf_state='published',
    base_image_path=__file__
)
```

Translations
------------

If you are using plone.app.multilingual and creating items from a folder,
you can link translations using `translations.csv` in this format::

```csv
canonical,translation
/de/path/to/canonical,/en/path/to/translation
```

Development
-----------

Requirements:

- Python 3
- venv

Setup:

```shell
  make
```

Run Static Code Analysis:

```shell
  make lint
```

Run Unit / Integration Tests:

```shell
  make test
```
