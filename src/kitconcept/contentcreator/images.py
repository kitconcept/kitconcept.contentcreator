from kitconcept.contentcreator.dummy_image import generate_image
from plone.namedfile.file import NamedBlobFile
from plone.namedfile.file import NamedBlobImage
from six import BytesIO

import magic
import os


def process_local_images(data, obj, base_image_path):
    get_file_type = magic.Magic(mime=True)
    image_fieldnames_added = []

    if data.get("set_dummy_image", False) and isinstance(
        data.get("set_dummy_image"), list
    ):
        new_file = BytesIO()
        generate_image().save(new_file, "png")
        new_file = new_file if type(new_file) == str else new_file.getvalue()
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
        new_file = new_file if type(new_file) == str else new_file.getvalue()
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
            new_file = open(os.path.join(base_image_path, image_data[1]), "rb")
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
            new_file = open(os.path.join(base_image_path, image_data[1]), "rb")
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
        new_file = open(os.path.join(base_image_path, data.get("set_local_file")), "rb")
        # Get the correct content-type
        content_type = get_file_type.from_buffer(new_file.read())
        new_file.seek(0)

        obj.file = NamedBlobFile(
            data=new_file.read(),
            filename=data.get("set_local_file"),
            contentType=content_type,
        )

    return image_fieldnames_added
