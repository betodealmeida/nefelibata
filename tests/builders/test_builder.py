from pathlib import Path

import pytest
from freezegun import freeze_time
from nefelibata.builders import Builder
from nefelibata.builders import get_builders
from nefelibata.builders import Scope
from nefelibata.post import Post

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


class MockBuilder(Builder):

    scopes = [Scope.POST]


def make_dummy_builder(scope):
    return type("SomeBuilder", (Builder,), {"scopes": [scope]})


class MockEntryPoint:
    def __init__(self, name: str, builder: Builder):
        self.name = name
        self.builder = builder

    def load(self) -> Builder:
        return self.builder


def test_get_builders(mocker):
    entry_points = [
        MockEntryPoint("test1", make_dummy_builder(Scope.POST)),
        MockEntryPoint("test2", make_dummy_builder(Scope.SITE)),
    ]
    mocker.patch("nefelibata.builders.iter_entry_points", return_value=entry_points)

    config = {
        "url": "https://blog.example.com/",
        "language": "en",
        "builders": ["test1", "test2"],
        "test1": {},
        "test2": {},
    }

    root = Path("/path/to/blog")
    builders = get_builders(root, config, Scope.POST)
    assert len(builders) == 1
    assert builders[0].scopes == [Scope.POST]


def test_wrong_scope(mock_post):
    config = {}

    root = Path("/path/to/blog")
    post_builder = make_dummy_builder([Scope.POST])(root, config)
    with pytest.raises(Exception) as excinfo:
        post_builder.process_site()

    assert str(excinfo.value) == 'Scope "site" not supported by SomeBuilder'

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: test
        keywords: test
        summary: A simple test

        Hello, there!
        """,
        )

    site_builder = make_dummy_builder([Scope.SITE])(root, config)
    with pytest.raises(Exception) as excinfo:
        site_builder.process_post(post)

    assert str(excinfo.value) == 'Scope "post" not supported by SomeBuilder'
