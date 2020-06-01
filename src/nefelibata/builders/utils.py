import hashlib


def hash_n(text: bytes, numbers: int = 10) -> int:
    """Hash a string into a number between 0 and `numbers-1`.
    """
    return int(hashlib.md5(text).hexdigest(), 16) % numbers
