from nefelibata.builders.utils import hash_n

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


def test_hash_n():
    assert hash_n(b"one", 1) == 0
    assert hash_n(b"two", 1) == 0
    assert hash_n(b"three", 10) == 2
