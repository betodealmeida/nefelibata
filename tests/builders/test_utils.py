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
    assert random_color("one") == "#9c5d67"
    assert random_color("two") == "#7a65a3"
    assert random_color("three") == "#697546"
    assert random_color("one", rgb=(0, 0, 0)) == "#ffffff"
