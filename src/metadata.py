from PIL import Image


def strip_metadata(image: Image.Image) -> Image.Image:
    clean = Image.new(image.mode, image.size)
    clean.paste(image)
    clean.info = {}
    return clean
