import hashlib
from colorsys import hls_to_rgb
from typing import List
from typing import Tuple


def hash_n(text: bytes, numbers: int = 10) -> int:
    """Hash a string into a number between 0 and `numbers-1`.
    """
    return int(hashlib.md5(text).hexdigest(), 16) % numbers


def luminance(rgb: Tuple[float, float, float]) -> float:
    coefficients: List[float] = []
    for value in rgb:
        if value <= 0.03928:
            value = value / 12.92
        else:
            value = (value + 0.055) ** 2.4
        coefficients.append(value)

    return (
        coefficients[0] * 0.2126 + coefficients[1] * 0.7152 + coefficients[2] * 0.0722
    )


def contrast(
    rgb1: Tuple[float, float, float], rgb2: Tuple[float, float, float],
) -> float:
    value = (luminance(rgb1) + 0.05) / (luminance(rgb2) + 0.05)
    return value if value >= 1 else 1 / value


def random_color(
    text: str, target_contrast: float = 5, rgb: Tuple[float, float, float] = (1, 1, 1),
) -> str:
    """Generate a random color based on the hash of the string.
    """
    hue = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16) / (2 ** 128)
    saturation = 0.25
    lightness = 1.0

    while True:
        candidate = hls_to_rgb(hue, lightness, saturation)
        if contrast(rgb, candidate) >= target_contrast:
            break
        lightness -= 0.01

    return "#%02x%02x%02x" % tuple(int(v * 255) for v in candidate)
