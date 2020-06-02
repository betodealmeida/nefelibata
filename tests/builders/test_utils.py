import pytest
from nefelibata.builders.utils import hash_n
from nefelibata.builders.utils import random_color

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


def test_hash_n():
    assert hash_n(b"one", 1) == 0
    assert hash_n(b"two", 1) == 0
    assert hash_n(b"three", 10) == 2


def test_random_color():
    assert random_color("one") == "#5d000e"
    assert random_color("two") == "#1e005d"
    assert random_color("three") == "#455d00"

    assert random_color("one", contrast_luminance=0) == "#59000d"

    with pytest.raises(Exception) as excinfo:
        random_color("one", contrast_luminance=0.5) == "59000d"
    assert str(excinfo.value) == "Computed luminance outside bounds: 2.43"
