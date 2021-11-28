# -*- coding: utf-8 -*-
from Acquisition import aq_base
from Acquisition.interfaces import IAcquirer
from kitconcept.contentcreator.dummy_image import generate_image
from OFS.Image import Image
from plone import api
from plone.app.dexterity import behaviors
from plone.dexterity.interfaces import IDexterityContent
from plone.namedfile.file import NamedBlobFile
from plone.namedfile.file import NamedBlobImage
from plone.portlets.interfaces import IPortletAssignmentSettings
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes
from Products.CMFPlone.utils import safe_hasattr
from six import BytesIO
from six import MAXSIZE
from zope.component import queryMultiAdapter
from zope.event import notify
from zope.globalrequest import getRequest
from zope.lifecycleevent import ObjectCreatedEvent
from zExceptions import NotFound
from kitconcept.contentcreator.scales import plone_scale_generate_on_save
from plone.restapi.behaviors import IBlocks
from plone.app.content.interfaces import INameFromTitle
from zope.container.interfaces import INameChooser
from DateTime import DateTime

from plone.restapi.interfaces import IDeserializeFromJson
from zope.component import getMultiAdapter
from plone.dexterity.utils import iterSchemata
from plone.restapi.interfaces import IFieldSerializer
from plone.restapi.services.content.utils import add
from plone.restapi.services.content.utils import create

import json
import logging
import magic
import os
import pkg_resources


try:
    pkg_resources.get_distribution("Products.Archetypes")
    from Products.Archetypes.interfaces import IBaseObject

    ARCHETYPES_PRESENT = True
except pkg_resources.DistributionNotFound:  # pragma: no restapi
    ARCHETYPES_PRESENT = False


try:
    from Products.CMFPlone.utils import get_installer
except ImportError:
    get_installer = None

logger = logging.getLogger("kitconcept.contentcreator")

# Removing description block from the creator, bring it back parameterized if
# required
DEFAULT_BLOCKS = {
    "d3f1c443-583f-4e8e-a682-3bf25752a300": {"@type": "title"},
    # "35240ad8-3625-4611-b76f-03471bcf6b34": {"@type": "description"},
    "7624cf59-05d0-4055-8f55-5fd6597d84b0": {"@type": "slate"},
}
DEFAULT_BLOCKS_LAYOUT = {
    "items": [
        "d3f1c443-583f-4e8e-a682-3bf25752a300",
        # "35240ad8-3625-4611-b76f-03471bcf6b34",
        "7624cf59-05d0-4055-8f55-5fd6597d84b0",
    ]
}


def print_error(error_string):  # RED
    print("\033[31mERROR: {}\033[0m".format(error_string))
    logger.error("{}".format(error_string))


def load_json(path, base_path=None):
    """Load JSON from a file.

    :param path: Absolute or relative path to the JSON file. If relative,
                 you might want to use the next parameter too.
    :type path: string
    :param base_path: Base path, from which the relative path is calculated.
                      From the calling module, you will pass ``__file__`` to
                      this argument.
    :returns: Decoded JSON structure as Python dictionary.
    :rtype: dict
    """
    if base_path:
        path = os.path.join(os.path.dirname(base_path), path)
    content_json = ""
    with open(path, "r") as file_handle:
        content_json = json.loads(file_handle.read())

    return content_json


def add_criterion(topic, index, criterion, value=None):
    index = index.encode("utf-8")
    criterion = criterion.encode("utf-8")
    name = "{0}_{1}".format(index, criterion)
    topic.addCriterion(index, criterion)
    crit = topic.getCriterion(name)

    # TODO: Add extra parameter to the criterion creation for these criterion types
    if criterion == "ATDateRangeCriterion":
        crit.setStart("2019/02/20 13:55:00 GMT-3")
        crit.setEnd("2019/02/22 13:55:00 GMT-3")
    elif criterion == "ATSortCriterion":
        crit.setReversed(True)
    elif criterion == "ATBooleanCriterion":
        crit.setBool(True)

    if value is not None:
        crit.setValue(value)


def create_portlets(obj, portlets):
    if not portlets:
        return

    # Avoid portlet duplication
    for manager_name in portlets:
        mapping = obj.restrictedTraverse("++contextportlets++{0}".format(manager_name))
        for m in mapping.keys():
            del mapping[m]
    # Avoid portlet duplication

    for manager_name in portlets:
        for data in portlets[manager_name]:
            mapping = obj.restrictedTraverse(
                "++contextportlets++{0}".format(manager_name)
            )
            addview = mapping.restrictedTraverse("+/{0}".format(data["type"]))
            if getattr(addview, "createAndAdd", False):
                addview.createAndAdd(data=data["assignment"])
            else:  # Some portlets don't have assignment
                addview.create()
            assignment = list(mapping.values())[-1]
            settings = IPortletAssignmentSettings(assignment)
            settings["visible"] = data["visible"]


def set_exclude_from_nav(obj):
    """Set image field in object on both, Archetypes and Dexterity."""
    try:
        obj.setExcludeFromNav(True)  # Archetypes
    except AttributeError:
        # Dexterity
        obj.exclude_from_nav = True
    finally:
        obj.reindexObject(idxs=["exclude_from_nav"])


def disable_content_type(portal, fti_id):
    portal_types = getToolByName(portal, "portal_types")
    document_fti = getattr(portal_types, fti_id)
    document_fti.global_allow = False


def enable_content_type(portal, fti_id):
    portal_types = getToolByName(portal, "portal_types")
    document_fti = getattr(portal_types, fti_id)
    document_fti.global_allow = True


def get_lang_from_lrf(container, langs):
    for segment in container.getPhysicalPath():
        if segment in langs:
            return segment


def create_object(path, is_folder=False):
    """Recursively create object and folder structure if necessary"""
    obj = api.content.get(path=path)
    if obj is not None:
        return obj

    path_parent, obj_id = path.rsplit("/", 1)
    if path_parent == "":
        parent = api.portal.get()
    else:
        parent = create_object(path_parent, is_folder=True)

    logger.info(f"{path} - create")

    obj = api.content.create(
        container=parent, type="Folder" if is_folder else "Document", id=obj_id
    )
    api.content.transition(obj=obj, transition="publish")
    return obj


def create_item_runner(  # noqa
    container,
    content_structure,
    base_image_path=os.path.dirname(__file__),
    auto_id=False,
    default_lang=None,
    default_wf_state=None,
    ignore_wf_types=["Image", "File"],
    logger=logger,
    do_not_edit_if_modified_after=None,
):
    """Create Dexterity contents from plone.restapi compatible structures.

    :param container: The context in which the item should be created.
    :type container: Plone content object
    :param content_structure: Python dictionary with content structure.
    :type content_structure: dict
    :param default_lang: Default language.
    :type default_lang: string
    :param default_wf_state: Default workflow state.
    :type default_wf_state: string
    :param ignore_wf_types: Ignore to apply the workflow transition if item is
                            one of these types.
    :type ignore_wf_types: list (default: ['Image', 'File'])
    :param logger: Logger to use.
    :type logger: Python logging instance.

    The datastructure of content defined by plone.restapi:

    https://plonerestapi.readthedocs.io/en/latest/content.html#creating-a-resource-with-post

    [
        {
            "type": "",
            "id": "",
            "title": "",
            "description": "",
            "opts": {
                "default_page": "",
                "default_view": "",
                "exclude_from_nav": "",
                "local_roles": {},
                "locally_allowed_types": [],
                "locally_allowed_types": [],
                "immediately_allowed_types": [],
            },
            "items": []
        }
    ]

    Use the same structure for each child. Leave out, what you don't need.
    """

    request = getRequest()
    portal = api.portal.get()

    for data in content_structure:
        type_ = data.get("@type", None)
        id_ = data.get("id", None)
        title = data.get("title", None)

        if not type_:
            logger.warn("Property '@type' is required")
            continue

        if container.portal_type == "Topic":
            field = data.get("field", None)
            value = data.get("value", None)
            add_criterion(container, field, type_, value)
            continue

        # PFG
        if type_ in ["FormSelectionField", "FormMultiSelectionField"]:
            container.fgVocabulary = data.get("fgVocabulary", [])
            continue

        create_object = False
        if container.get(id_, False):
            # We check if the object is already created, if so we edit it
            obj = container[id_]
        else:
            # if don't we create it
            try:
                obj = create(container, type_, id_=id_, title=title)
                create_object = True
            except Exception as e:
                print_error(
                    "Can not create object {} ({}) in {}, because of {}".format(
                        id_, type_, "/".join(container.getPhysicalPath()), e
                    )
                )
                continue
        if (
            not create_object
            and do_not_edit_if_modified_after is not None
            and DateTime(obj.modification_date)
            > DateTime(do_not_edit_if_modified_after)
        ):
            continue

        try:
            # Acquisition wrap temporarily to satisfy things like vocabularies
            # depending on tools
            temporarily_wrapped = False
            if IAcquirer.providedBy(obj) and not safe_hasattr(obj, "aq_base"):
                obj = obj.__of__(container)
                temporarily_wrapped = True

            deserializer = queryMultiAdapter((obj, request), IDeserializeFromJson)

            if deserializer is None:
                print_error("Cannot deserialize type {}".format(obj.portal_type))
                continue

            # defaults
            if not data.get("language"):
                language_tool = api.portal.get_tool("portal_languages")
                supported_langs = language_tool.getSupportedLanguages()

                if get_installer:
                    installer = get_installer(portal, request)
                else:
                    installer = api.portal.get_tool("portal_quickinstaller")

                if (
                    installer.isProductInstalled("plone.app.multilingual")
                    and len(supported_langs) > 1
                    and not obj.language
                ):
                    # If pam, supported langs are two or more, and obj has no language set
                    # get language from path and set it
                    data["language"] = get_lang_from_lrf(container, supported_langs)
                else:
                    # If object does not have already language, and default_lang is set
                    if not obj.language and default_lang:
                        data["language"] = default_lang

            if not data.get("review_state") and obj.portal_type not in ignore_wf_types:
                data["review_state"] = default_wf_state

            # Populate default blocks if the content has the behavior enabled
            # And no blocks in the creation or in the existing object
            if (
                hasattr(obj, "blocks")
                and not data.get("blocks", False)
                and not obj.blocks
            ):
                obj.blocks = DEFAULT_BLOCKS
                obj.blocks_layout = DEFAULT_BLOCKS_LAYOUT

            get_file_type = magic.Magic(mime=True)
            # Populate image if any
            image_fieldnames_added = []
            if ARCHETYPES_PRESENT and IBaseObject.providedBy(obj):
                if data.get("set_dummy_image", False):
                    new_file = BytesIO()
                    generate_image().save(new_file, "png")
                    obj.setImage(Image("test.png", "test.png", new_file))
                if data.get("set_local_image", False):
                    new_file = open(
                        os.path.join(base_image_path, data.get("set_local_image")), "rb"
                    )
                    obj.setImage(new_file.read())
                if data.get("set_dummy_file", False):
                    new_file = BytesIO()
                    generate_image().save(new_file, "png")
                    obj.setFilename("test.png")
                    obj.setFile(new_file)
                    obj.setFormat("image/png")
                if data.get("set_local_file", False):
                    new_file = open(
                        os.path.join(base_image_path, data.get("set_local_image")), "rb"
                    )
                    obj.setFilename(os.path.basename(data.get("set_local_image")))
                    obj.setFile(new_file.read())
                    obj.setFormat("image/png")

            if IDexterityContent.providedBy(obj):
                if data.get("set_dummy_image", False) and isinstance(
                    data.get("set_dummy_image"), list
                ):
                    new_file = BytesIO()
                    generate_image().save(new_file, "png")
                    new_file = (
                        new_file if type(new_file) == str else new_file.getvalue()
                    )
                    for image_field in data["set_dummy_image"]:
                        setattr(
                            obj,
                            image_field,
                            NamedBlobImage(data=new_file, contentType="image/png"),
                        )

                    image_fieldnames_added + data["set_dummy_image"]

                elif data.get("set_dummy_image", False) and isinstance(
                    data.get("set_dummy_image"), bool
                ):
                    # Legacy behavior, set_dummy_image is a boolean
                    obj.image = NamedBlobImage(
                        data=generate_image().tobytes(), contentType="image/png"
                    )

                    image_fieldnames_added.append("image")

                if data.get("set_dummy_file", False) and isinstance(
                    data.get("set_dummy_file"), list
                ):
                    new_file = BytesIO()
                    generate_image().save(new_file, "png")
                    new_file = (
                        new_file if type(new_file) == str else new_file.getvalue()
                    )
                    for image_field in data["set_dummy_file"]:
                        setattr(
                            obj,
                            image_field,
                            NamedBlobFile(data=new_file, contentType="image/png"),
                        )

                elif data.get("set_dummy_file", False) and isinstance(
                    data.get("set_dummy_file"), bool
                ):
                    # Legacy behavior, set_dummy_file is a boolean
                    obj.file = NamedBlobFile(
                        data=generate_image().tobytes(), contentType="image/png"
                    )

                if data.get("set_local_image", False) and isinstance(
                    data.get("set_local_image"), dict
                ):
                    for image_data in data["set_local_image"].items():
                        new_file = open(
                            os.path.join(base_image_path, image_data[1]), "rb"
                        )
                        # Get the correct content-type
                        content_type = get_file_type.from_buffer(new_file.read())
                        new_file.seek(0)

                        setattr(
                            obj,
                            image_data[0],
                            NamedBlobImage(
                                data=new_file.read(),
                                filename=image_data[1],
                                contentType=content_type,
                            ),
                        )

                        image_fieldnames_added.append(image_data[0])

                elif data.get("set_local_image", False) and isinstance(
                    data.get("set_local_image"), str
                ):
                    new_file = open(
                        os.path.join(base_image_path, data.get("set_local_image")), "rb"
                    )
                    # Get the correct content-type
                    content_type = get_file_type.from_buffer(new_file.read())
                    new_file.seek(0)

                    obj.image = NamedBlobImage(
                        data=new_file.read(),
                        filename=data.get("set_local_image"),
                        contentType=content_type,
                    )

                    image_fieldnames_added.append("image")

                if data.get("set_local_file", False) and isinstance(
                    data.get("set_local_file"), dict
                ):
                    for image_data in data["set_local_file"].items():
                        new_file = open(
                            os.path.join(base_image_path, image_data[1]), "rb"
                        )
                        # Get the correct content-type
                        content_type = get_file_type.from_buffer(new_file.read())
                        new_file.seek(0)

                        setattr(
                            obj,
                            image_data[0],
                            NamedBlobFile(
                                data=new_file.read(),
                                filename=image_data[1],
                                contentType=content_type,
                            ),
                        )

                elif data.get("set_local_file", False) and isinstance(
                    data.get("set_local_file"), str
                ):
                    new_file = open(
                        os.path.join(base_image_path, data.get("set_local_file")), "rb"
                    )
                    # Get the correct content-type
                    content_type = get_file_type.from_buffer(new_file.read())
                    new_file.seek(0)

                    obj.file = NamedBlobFile(
                        data=new_file.read(),
                        filename=data.get("set_local_file"),
                        contentType=content_type,
                    )

            deserializer(validate_all=True, data=data, create=True)

            if temporarily_wrapped:
                obj = aq_base(obj)

            path = "/".join(obj.getPhysicalPath())

            if create_object:
                if not getattr(deserializer, "notifies_create", False):
                    notify(ObjectCreatedEvent(obj))

                obj = add(container, obj, rename=not bool(id_))
                for image_fieldname in image_fieldnames_added:
                    logger.debug(
                        "{} - generating image scales for {} field".format(
                            "/".join(obj.getPhysicalPath()), image_fieldname
                        )
                    )
                    plone_scale_generate_on_save(obj, request, image_fieldname)

            # Set UUID - TODO: add to p.restapi
            if (
                data.get("UID", False)
                and ARCHETYPES_PRESENT
                and IBaseObject.providedBy(obj)
            ):
                obj._setUID(data.get("UID"))
                obj.reindexObject(idxs=["UID"])
            else:
                if data.get("UID"):
                    setattr(obj, "_plone.uuid", data.get("UID"))
                    obj.reindexObject(idxs=["UID"])

            # Set workflow
            if (
                data.get("review_state", False)
                and obj.portal_type not in ignore_wf_types
            ):  # noqa
                api.content.transition(obj=obj, to_state=data.get("review_state"))
                if data.get("review_state") == "published" and not data.get(
                    "effective", False
                ):
                    # Side-effect if review_state is published, always set the effective date
                    obj.effective_date = DateTime()

            # set default
            opts = data.get("opts", {})
            if opts.get("default_page", False):
                container.setDefaultPage(obj.id)
            default_view = opts.get("default_view", False)
            if default_view:
                obj.setLayout(default_view)
            if opts.get("exclude_from_nav", False):
                set_exclude_from_nav(obj)

            id_ = obj.id  # get the real id
            path = "/".join(obj.getPhysicalPath())

            if create_object:
                logger.info(f"{path} - created")
            else:
                logger.info(f"{path} - edited")

            # CONSTRAIN TYPES
            locally_allowed_types = opts.get("locally_allowed_types", False)
            immediately_allowed_types = opts.get(
                "immediately_allowed_types", False
            )  # noqa
            if locally_allowed_types or immediately_allowed_types:
                be = ISelectableConstrainTypes(obj, None)
                if be:
                    be.setConstrainTypesMode(behaviors.constrains.ENABLED)
                    if locally_allowed_types:
                        be.setLocallyAllowedTypes = locally_allowed_types
                        logger.warn(
                            "{0} - locally_allowed_types {1}".format(
                                path, locally_allowed_types
                            )
                        )  # noqa
                    if immediately_allowed_types:
                        be.setImmediatelyAddableTypes = (
                            immediately_allowed_types  # noqa
                        )
                        logger.warn(
                            "{0} - immediately_allowed_types {1}".format(
                                path, immediately_allowed_types
                            )
                        )  # noqa

            create_portlets(obj, data.get("portlets", []))

            # create local roles
            for user, roles in opts.get("local_roles", {}).items():
                obj.manage_setLocalRoles(user, roles)

            # reindex object
            obj.reindexObject()

        except Exception as e:
            container_path = "/".join(container.getPhysicalPath())
            message = 'Could not edit the fields and properties for (type: "{0}", container: "{1}", id: "{2}", title: "{3}") exception: {4}'
            print_error(message.format(type_, container_path, id_, title, e))
            continue

        # Call recursively
        create_item_runner(
            obj,
            content_structure=data.get("items", []),
            default_lang=default_lang,
            default_wf_state=default_wf_state,
            ignore_wf_types=ignore_wf_types,
            logger=logger,
            base_image_path=base_image_path,
        )


def get_objects_created(container, content_structure):
    paths = []

    for data in content_structure:
        id_ = data.get("id", None)
        obj = container[id_]

        paths.append("/".join(obj.getPhysicalPath()))
        result = get_objects_created(obj, content_structure=data.get("items", []))

        if result:
            paths = paths + result
        return paths


def refresh_objects_created_by_structure(container, content_structure):
    def deserialize(obj, blocks=None, validate_all=False):
        request = getRequest()
        request["BODY"] = json.dumps({"blocks": blocks})
        deserializer = getMultiAdapter((obj, request), IDeserializeFromJson)

        return deserializer(validate_all=validate_all)

    def serialize(context):
        request = getRequest()
        fieldname = "blocks"
        for schema in iterSchemata(context):
            if fieldname in schema:
                field = schema.get(fieldname)
                break

        serializer = getMultiAdapter((field, context, request), IFieldSerializer)
        return serializer()

    def get_content_by_data(data, container):
        type_ = data.get("@type", None)
        id_ = data.get("id", None)
        title = data.get("title", None)

        obj = create(container, type_, id_=id_, title=title)
        chooser = INameChooser(container)
        # INameFromTitle adaptable objects should not get a name
        # suggestion. NameChooser would prefer the given name instead of
        # the one provided by the INameFromTitle adapter.
        suggestion = None
        name_from_title = INameFromTitle(obj, None)
        if name_from_title is None:
            suggestion = obj.Title()
        id_ = chooser.chooseName(suggestion, obj)
        original = id_[:-2]
        return container.get(original, None)

    for data in content_structure:
        id_ = data.get("id", None)
        if not id_:
            obj = get_content_by_data(data, container)
            if not obj:
                print_error(
                    "id can't be guessed for {0} in container {1}".format(
                        "/".join(container.getPhysicalPath()), data["title"]
                    )
                )
                return
        else:
            obj = container.get(id_, None)

        if obj and IBlocks.providedBy(obj):
            blocks_serialized = serialize(obj)
            deserialize(obj, blocks_serialized)

        if obj:
            refresh_objects_created_by_structure(
                obj, content_structure=data.get("items", [])
            )


def refresh_objects_created_by_file(filepath, file_):
    def deserialize(obj, blocks=None, validate_all=False):
        request = getRequest()
        request["BODY"] = json.dumps({"blocks": blocks})
        deserializer = getMultiAdapter((obj, request), IDeserializeFromJson)

        return deserializer(validate_all=validate_all)

    def serialize(context):
        request = getRequest()
        fieldname = "blocks"
        for schema in iterSchemata(context):
            if fieldname in schema:
                field = schema.get(fieldname)
                break

        serializer = getMultiAdapter((field, context, request), IFieldSerializer)
        return serializer()

    splitted_path = os.path.splitext(file_)[0].split(".")
    path = "/" + "/".join(splitted_path[:-1])
    id_ = splitted_path[-1]
    try:
        container = api.content.get(path=path)
    except NotFound:
        print_error('Could not look up container under "{}"'.format(path))
        return

    obj = container.get(id_, None)
    if obj and IBlocks.providedBy(obj):
        blocks_serialized = serialize(obj)
        deserialize(obj, blocks_serialized)


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
):
    """
    Main entry point for the content creator. It allows to have a structure like:
    |-content_creator
        |- content.json
        |- siteroot.json
        |- de.mysection.json
        |- ...
    |-content_images

    using these names (for both files and folders) as sensible defaults.

    and creates the content in a tree like from `content.json` using the runner, and
    object by object using the standalone json files.

    In your setuphandlers.py you need to:

    from kitconcept.contentcreator.creator import content_creator_from_folder
    ...

    content_creator_from_folder()

    in the `import_content` method (triggered by GenericSetup on plonesite recipe install)
    or in a place that it gets properly called.

    The path and id of the standalone objects creation are determined by the name of the file like in

    de.beispiele.bildergroessen.json

    The file is a p.restapi JSON syntax. This method reads all the files and kick the
    runner in for process them.

    """
    # enable content non-globally addable types just for initial content
    # creation
    portal = api.portal.get()
    for content_type in temp_enable_content_types:
        enable_content_type(portal, content_type)

    folder = os.path.join(os.path.dirname(__file__), folder_name)

    # Get files in the right order
    def sort_key(item):
        return (
            len(item.split(".")[:-1]),  # First folders
            custom_order.index(item)
            if item in custom_order
            else MAXSIZE,  # Custom order
            item.lower(),  # Than alphabetically
        )

    files = sorted(os.listdir(folder), key=sort_key)
    has_content_json = False
    # has_siteroot_json = False

    for file_ in files:
        # If a content.json is found, proceed as if it contains a normal json arrayed
        # structure
        if file_ == "content.json":
            has_content_json = True
            logger.info("content.json file found, creating content")
            content_structure = load_json(os.path.join(folder, "content.json"))
            create_item_runner(
                api.portal.get(),
                content_structure,
                default_lang=default_lang,
                default_wf_state=default_wf_state,
                ignore_wf_types=ignore_wf_types,
                logger=logger,
                base_image_path=base_image_path,
                do_not_edit_if_modified_after=do_not_edit_if_modified_after,
            )
            continue
        elif file_ == "siteroot.json":
            logger.info("Site root info found, applying changes")
            root_info = load_json(os.path.join(folder, "siteroot.json"))
            modify_siteroot(root_info)
            continue
        # blacklist "images" folder
        elif file_ == "images":
            continue

        # ex.: file_ = 'de.ueber-uns.json'
        filepath = os.path.join(folder, file_)
        # ex.: path = '/de'
        splitted_path = os.path.splitext(file_)[0].split(".")
        path = "/" + "/".join(splitted_path[:-1])
        try:
            container = api.content.get(path=path)
        except NotFound:
            print_error('Could not look up container under "{}"'.format(path))
        if container is None:
            container = create_object(path)
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            data["id"] = splitted_path[-1]
            create_item_runner(
                container,
                [data],
                default_lang=default_lang,
                default_wf_state=default_wf_state,
                ignore_wf_types=ignore_wf_types,
                logger=logger,
                base_image_path=base_image_path,
                do_not_edit_if_modified_after=do_not_edit_if_modified_after,
            )
        except ValueError as e:
            print_error('Error in file structure: "{0}": {1}'.format(filepath, e))
        except FileNotFoundError as e:
            print_error('Error in file structure: "{0}": {1}'.format(filepath, e))
        except Exception as e:  # noqa
            print_error('Error in file structure: "{0}": {1}'.format(filepath, e))

    # After creation, we refresh all the content created to update resolveuids
    if len(files) > 0:
        logger.info("Refreshing content serialization after creation...")
    for file_ in files:
        filepath = os.path.join(folder, file_)
        refresh_objects_created_by_file(filepath, file_)
    if has_content_json:
        logger.info(
            "Refreshing structured (content.json) content serialization after creation..."
        )
        refresh_objects_created_by_structure(api.portal.get(), content_structure)

    for content_type in temp_enable_content_types:
        disable_content_type(portal, content_type)


def modify_siteroot(root_info):
    portal = api.portal.get()
    blocks = root_info["blocks"]
    blocks_layout = root_info["blocks_layout"]

    if not getattr(portal, "blocks", False):
        portal.manage_addProperty("blocks", json.dumps(blocks), "string")
    else:
        portal.blocks = json.dumps(blocks)

    if not getattr(portal, "blocks_layout", False):
        portal.manage_addProperty(
            "blocks_layout", json.dumps(blocks_layout), "string"
        )  # noqa
    else:
        portal.blocks_layout = json.dumps(blocks_layout)
