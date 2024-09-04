import cv2
import numpy as np
from PIL import ImageDraw, ImageFont, Image


def add_text_f(img_path: str, text: str) -> np.array:
    """Adds text to an image using the Pillow library.

    Args:
        img_path: The path to the image file.
        text: The text to add to the image.

    Returns:
        A NumPy array containing the image with the added text.
    """
    img: Image = Image.fromarray(cv2.imread(img_path))  # Don't want to use context manager lol
    font: ImageFont = ImageFont.truetype("resources/data/RobotoMono-Regular.ttf", size=16)
    artist: ImageDraw = ImageDraw.Draw(img)
    artist.text((img.width / 2 - font.getlength(text) / 2, img.height - 30), text, font=font)


def add_text(img: np.ndarray, text: str, loc: tuple[int] | list[int]) -> np.ndarray:
    """Adds text to an image using OpenCV.

    Args:
        img: The image as a NumPy array.
        text: The text to add to the image.
        loc: A tuple (x, y) representing the location to place the text.

    Returns:
        A NumPy array containing the image with the added text.
    """
    return cv2.putText(
        img=img,
        text=text,
        org=loc,
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=0.75,
        color=[0, 0, 0],  # This uses BGR??
        thickness=2,
        lineType=cv2.LINE_8
    )
