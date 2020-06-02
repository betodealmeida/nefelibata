from pathlib import Path

from nefelibata.publishers import get_publishers
from nefelibata.publishers import Publisher

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


def make_dummy_publisher(name):
    return type("SomePublisher", (Publisher,), {})


class TestEntryPoint:
    def __init__(self, name: str, publisher: Publisher):
        self.name = name
        self.publisher = publisher

    def load(self) -> Publisher:
        return self.publisher


def test_get_publishers(mock_post, mocker):
    entry_points = [
        TestEntryPoint("test1", make_dummy_publisher("Test1")),
        TestEntryPoint("test2", make_dummy_publisher("Test2")),
    ]
    mocker.patch("nefelibata.publishers.iter_entry_points", return_value=entry_points)

    config = {
        "url": "https://blog.example.com/",
        "language": "en",
        "publish-to": ["test2"],
        "test1": {},
        "test2": {},
    }

    publishers = get_publishers(config)
    assert len(publishers) == 1
    assert publishers[0].__class__ is entry_points[1].publisher


def test_get_publishers_string(mock_post, mocker):
    entry_points = [
        TestEntryPoint("test1", make_dummy_publisher("Test1")),
        TestEntryPoint("test2", make_dummy_publisher("Test2")),
    ]
    mocker.patch("nefelibata.publishers.iter_entry_points", return_value=entry_points)

    config = {
        "url": "https://blog.example.com/",
        "language": "en",
        "publish-to": "test2",
        "test1": {},
        "test2": {},
    }

    publishers = get_publishers(config)
    assert len(publishers) == 1
    assert publishers[0].__class__ is entry_points[1].publisher
