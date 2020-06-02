import hashlib
from colorsys import hls_to_rgb


def hash_n(text: bytes, numbers: int = 10) -> int:
    """Hash a string into a number between 0 and `numbers-1`.
    """
    return int(hashlib.md5(text).hexdigest(), 16) % numbers


def random_color(
    text: str, contrast: float = 4.5, contrast_luminance: float = 1,
) -> str:
    """Generate a random color based on the hash of the string.
    """
    hue = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16) / (2 ** 128)
    saturation = 1

    if contrast_luminance > 0.5:
        luminance = ((contrast_luminance + 0.05) / contrast) - 0.05
    else:
        luminance = (contrast_luminance + 0.05) * contrast - 0.05

    if not 0 <= luminance <= 1:
        raise Exception(f"Computed luminance outside bounds: {luminance:.2f}")

    rgb = hls_to_rgb(hue, luminance, saturation)
    return "#%02x%02x%02x" % tuple(int(v * 255) for v in rgb)
