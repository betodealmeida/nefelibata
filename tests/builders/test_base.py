"""
Tests for ``nefelibata.builders.base``.
"""
from pathlib import Path
from typing import Type

from pytest_mock import MockerFixture

from nefelibata.builders.base import Builder, get_builders
from nefelibata.post import Post
from nefelibata.typing import Config

from ..conftest import MockEntryPoint


def make_dummy_builder(class_name: str) -> Type[Builder]:
    """
    Make a dummy ``Builder`` derived class.
    """
    return type(class_name, (Builder,), {})


def test_get_builders(
    mocker: MockerFixture,
    make_entry_point: Type[MockEntryPoint],
    root: Path,
) -> None:
    """
    Test ``get_builders``.
    """
    DummyBuilder = make_dummy_builder("DummyBuilder")
    entry_points = [
        make_entry_point("builder", DummyBuilder),
    ]
    mocker.patch(
        "nefelibata.builders.base.iter_entry_points",
        return_value=entry_points,
    )

    config = {
        "builders": {
            "builder": {"plugin": "builder", "home": "https://example.com/"},
        },
    }
    builders = get_builders(root, config)
    assert len(builders) == 1
    assert isinstance(builders["builder"], DummyBuilder)


def test_builder_render(root: Path, config: Config) -> None:
    """
    Test the ``render`` method in ``Builder``.
    """
    builder = Builder(root, config, "https://example.com/")
    assert builder.render("test") == "test"


def test_builder_absolute_uri(root: Path, config: Config, post: Post) -> None:
    """
    Test the ``absolute_uri`` method in ``Builder``.
    """
    builder = Builder(root, config, "https://example.com/")
    builder.extension = ".html"
    assert builder.absolute_uri(post) == "https://example.com/first/index.html"
