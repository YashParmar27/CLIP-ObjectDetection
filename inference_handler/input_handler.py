from PIL import Image
import requests
from typing import List
from werkzeug.datastructures import FileStorage
import base64
from io import BytesIO

def prepare_input_images(path: str) -> List[Image.Image]:
    """
    Usage: Prepare input images from a file of image urls.
    Inputs: path for txt file containing urls.
    Outputs: List of PIL Image objects.
    """
    with open(path, 'r') as file:
        image_urls = file.read()
        
    urls = image_urls.split()
    
    images = []

    for url in urls:
        images.append(Image.open(requests.get(url, stream=True).raw))
    return images

def prepare_image_from_bytes(file: FileStorage) -> Image.Image:
    """
    Usage: Takes as input a binary image file and converts into PIL.Image.Image
    to be passed to the CLIP processor
    Input: A binary image file
    Output: A PIL Image object.
    """
    return Image.open(file.stream).convert("RGB")


def prepare_image_from_base64(base64_string):
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]

    image_data = base64.b64decode(base64_string)
    return Image.open(BytesIO(image_data)).convert("RGB")