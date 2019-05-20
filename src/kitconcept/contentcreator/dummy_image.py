from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import os


def generate_image(width=400, height=300):
    image = Image.new("RGB", (width, height), color=(73, 109, 137))
    draw = ImageDraw.Draw(image)
    draw.polygon(
        [(0, 0), (width - 1, 0), (width - 1, height - 1), (0, height - 1)],
        outline=(255, 255, 255),
    )

    text = u"{} x {}".format(width, height)
    font = ImageFont.truetype(
        os.path.join(os.path.dirname(__file__), "Poppins-Regular.ttf"), 20
    )
    center = (width / 2, height / 2)
    text_size = font.getsize(text)
    text_center = (center[0] - text_size[0] / 2, center[1] - text_size[1] / 2)
    draw.text(text_center, text, font=font, fill=(33, 22, 22))

    return image
