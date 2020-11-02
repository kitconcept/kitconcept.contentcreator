# -*- coding: utf-8 -*-
from ZODB.POSException import ConflictError
from zope.component import getMultiAdapter
from zope.component import getUtility

import logging
import transaction

try:
    from Products.CMFPlone.factory import _IMREALLYPLONE5  # noqa
except ImportError:
    PLONE_5 = False  # pragma: no cover
else:
    PLONE_5 = True  # pragma: no cover


logger = logging.getLogger(__name__)


def plone_scale_generate_on_save(context, request, fieldname):
    try:
        images = getMultiAdapter((context, request), name="images")
        try:
            scales = get_scale_infos()
        except ImportError:
            pass
        t = transaction.get()
        for name, actual_width, actual_height in scales:
            images.scale(fieldname, scale=name)
        image = getattr(context, fieldname, None)
        if image:  # REST API requires this scale to refer the original
            width, height = image.getImageSize()
            images.scale(fieldname, width=width, height=height, direction="thumbnail")
        msg = "/".join(
            filter(bool, ["/".join(context.getPhysicalPath()), "@@images", fieldname])
        )
        t.note(msg)
        t.commit()
    except ConflictError:
        msg = "/".join(
            filter(bool, ["/".join(context.getPhysicalPath()), "@@images", fieldname])
        )
        logger.warning("ConflictError. Scale not generated on save: " + msg)


def get_scale_infos():
    """Returns a list of (name, width, height) 3-tuples of the
    available image scales.
    """
    from Products.CMFCore.interfaces import IPropertiesTool

    if PLONE_5:
        from plone.registry.interfaces import IRegistry

        registry = getUtility(IRegistry)
        from Products.CMFPlone.interfaces import IImagingSchema

        imaging_settings = registry.forInterface(IImagingSchema, prefix="plone")
        allowed_sizes = imaging_settings.allowed_sizes

    else:
        ptool = getUtility(IPropertiesTool)
        image_properties = ptool.imaging_properties
        allowed_sizes = image_properties.getProperty("allowed_sizes")

    def split_scale_info(allowed_size):
        name, dims = allowed_size.split(" ")
        width, height = list(map(int, dims.split(":")))
        return name, width, height

    return [split_scale_info(size) for size in allowed_sizes]
