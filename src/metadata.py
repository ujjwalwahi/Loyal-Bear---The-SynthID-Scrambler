from PIL import Image


def strip_metadata(image: Image.Image) -> Image.Image:
    clean = Image.new(image.mode, image.size)
    clean.putdata(list(image.getdata()))
    clean.info = {}
    return clean
