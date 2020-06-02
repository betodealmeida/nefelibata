import hashlib
from colorsys import hls_to_rgb


def hash_n(text: bytes, numbers: int = 10) -> int:
    """Hash a string into a number between 0 and `numbers-1`.
    """
    return int(hashlib.md5(text).hexdigest(), 16) % numbers


def random_color(text: str) -> str:
    """Generate a random color based on the hash of the string.

    The color is generated with luminance 0.18 to ensure a contrast ratio of
    at least 4.5:1 against white text.
    """
    hue = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16) / (2 ** 128)
    saturation = 1
    luminance = 0.18

    rgb = hls_to_rgb(hue, luminance, saturation)
    return "#%02x%02x%02x" % tuple(int(v * 255) for v in rgb)
