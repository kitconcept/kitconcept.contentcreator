# -*- coding: utf-8 -*-
from Acquisition import aq_base
from Acquisition.interfaces import IAcquirer
from kitconcept.contentcreator.dummy_image import generate_image
from plone import api
from plone.app.dexterity import behaviors
from plone.dexterity.interfaces import IDexterityContent
from plone.namedfile.file import NamedBlobImage
from plone.portlets.interfaces import IPortletAssignmentSettings
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes
from Products.CMFPlone.utils import safe_hasattr
from zope.component import queryMultiAdapter
from zope.event import notify
from zope.globalrequest import getRequest
from zope.lifecycleevent import ObjectCreatedEvent
from six import StringIO
from OFS.Image import Image

import json
import logging
import os
import pkg_resources


try:
    pkg_resources.get_distribution("Products.Archetypes")
    from Products.Archetypes.interfaces import IBaseObject

    ARCHETYPES_PRESENT = True
except pkg_resources.DistributionNotFound:  # pragma: no restapi
    ARCHETYPES_PRESENT = False


try:
    pkg_resources.get_distribution("plone.restapi")
    from plone.restapi.interfaces import IDeserializeFromJson
    from plone.restapi.services.content.utils import add
    from plone.restapi.services.content.utils import create

    PRESTAPI_PRESENT = True
except pkg_resources.DistributionNotFound:  # pragma: no restapi
    PRESTAPI_PRESENT = False


logger = logging.getLogger("collective.contentcreator")


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
        crit.setStart(u"2019/02/20 13:55:00 GMT-3")
        crit.setEnd(u"2019/02/22 13:55:00 GMT-3")
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


def create_item_runner(
    container,
    content_structure,
    base_image_path=__file__,
    auto_id=False,
    default_lang=None,
    default_wf_state=None,
    ignore_wf_types=["Image", "File"],
    logger=logger,
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

        try:
            obj = create(container, type_, id_=id_, title=title)

            # set_image_field(obj, generate_jpeg(768, 768))

            # Acquisition wrap temporarily to satisfy things like vocabularies
            # depending on tools
            temporarily_wrapped = False
            if IAcquirer.providedBy(obj) and not safe_hasattr(obj, "aq_base"):
                obj = obj.__of__(container)
                temporarily_wrapped = True

            deserializer = queryMultiAdapter((obj, request), IDeserializeFromJson)

            if deserializer is None:
                logger.warn("Cannot deserialize type {}".format(obj.portal_type))
                continue

            # defaults
            if not data.get("language"):
                data["language"] = default_lang

            if not data.get("review_state") and obj.portal_type not in ignore_wf_types:
                data["review_state"] = default_wf_state

            # Populate image if any
            if ARCHETYPES_PRESENT and IBaseObject.providedBy(obj):
                if data.get("set_dummy_image", False):
                    new_file = StringIO()
                    generate_image().save(new_file, 'png')
                    obj.setImage(Image('test.png', 'test.png', new_file))
                if data.get("set_local_image", False):
                    image = open(
                        os.path.join(
                            os.path.dirname(base_image_path),
                            data.get("set_local_image"),
                        ),
                        "rb",
                    )
                    obj.setImage(image.read())

            if IDexterityContent.providedBy(obj) and hasattr(obj, "image"):
                if data.get("set_dummy_image", False):
                    obj.image = NamedBlobImage(
                        data=generate_image().tobytes(), contentType="image/png"
                    )
                if data.get("set_local_image", False):
                    image = open(
                        os.path.join(
                            os.path.dirname(base_image_path),
                            data.get("set_local_image"),
                        ),
                        "rb",
                    )
                    obj.image = NamedBlobImage(
                        data=image.read(), contentType="image/png"
                    )

            deserializer(validate_all=True, data=data, create=True)

            if temporarily_wrapped:
                obj = aq_base(obj)

            if not getattr(deserializer, "notifies_create", False):
                notify(ObjectCreatedEvent(obj))

            obj = add(container, obj, rename=not bool(id_))

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

            # set default
            opts = data.get("opts", {})
            if opts.get("default_page", False):
                container.setDefaultPage(obj.id)
            default_view = opts.get("default_view", False)
            if default_view:
                obj.setLayout(default_view)
            if opts.get("exclude_from_nav", False):
                set_exclude_from_nav(obj)

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
                            "{0}: locally_allowed_types {1}".format(
                                path, locally_allowed_types
                            )
                        )  # noqa
                    if immediately_allowed_types:
                        be.setImmediatelyAddableTypes = (
                            immediately_allowed_types
                        )  # noqa
                        logger.warn(
                            "{0}: immediately_allowed_types {1}".format(
                                path, immediately_allowed_types
                            )
                        )  # noqa

            id_ = obj.id  # get the real id
            path = "/".join(obj.getPhysicalPath())
            logger.info("{0}: created".format(path))

            create_portlets(obj, data.get("portlets", []))

            # create local roles
            for user, roles in opts.get("local_roles", {}).items():
                obj.manage_setLocalRoles(user, roles)
        except Exception as e:
            container_path = "/".join(container.getPhysicalPath())
            message = 'Could not create (type: "{0}", container: "{1}", id: "{2}") exception: {3}'  # noqa
            logger.warn(message.format(type_, container_path, id_, e.args[0]))
            continue

        # Call recursively
        create_item_runner(
            obj,
            content_structure=data.get("items", []),
            default_lang=default_lang,
            default_wf_state=default_wf_state,
            ignore_wf_types=ignore_wf_types,
            logger=logger,
        )
