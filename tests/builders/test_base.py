"""
Tests for ``nefelibata.builders.base``.
"""
from pathlib import Path
from typing import Type

import pytest
from pytest_mock import MockerFixture

from nefelibata.builders.base import Builder, Scope, get_builders
from nefelibata.typing import Config

from ..conftest import MockEntryPoint


def make_dummy_builder(class_name: str, scope: Scope) -> Type[Builder]:
    """
    Make a dummy ``Builder`` derived class.
    """
    return type(class_name, (Builder,), {"scopes": [scope]})


def test_get_builders(
    mocker: MockerFixture,
    make_entry_point: Type[MockEntryPoint],
    root: Path,
) -> None:
    """
    Test ``get_builders``.
    """
    SiteBuilder = make_dummy_builder("SiteBuilder", Scope.SITE)
    PostBuilder = make_dummy_builder("PostBuilder", Scope.POST)
    entry_points = [
        make_entry_point("site_builder", SiteBuilder),
        make_entry_point("post_builder", PostBuilder),
    ]
    mocker.patch(
        "nefelibata.builders.base.iter_entry_points",
        return_value=entry_points,
    )

    config = {
        "builders": [
            {"plugin": "site_builder", "home": "https://example.com/"},
            {"plugin": "post_builder", "home": "https://example.com/"},
        ],
    }
    builders = get_builders(root, config, Scope.POST)
    assert len(builders) == 1
    assert isinstance(builders["post_builder"], PostBuilder)

    config = {
        "builders": [
            {"invalid": "site_builder"},
            {"plugin": "post_builder"},
        ],
    }
    with pytest.raises(Exception) as excinfo:
        get_builders(root, config, Scope.POST)
    assert (
        str(excinfo.value)
        == """Invalid configuration, missing "plugin": {'invalid': 'site_builder'}"""
    )


def test_builder_render(root: Path, config: Config):
    """
    Test the ``render`` method in ``Builder``.
    """
    builder = Builder(root, config, "https://example.com/")
    assert builder.render("test") == "test"
