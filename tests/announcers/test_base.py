"""
Tests for ``nefelibata.announcers.base``.
"""

from pathlib import Path
from typing import Type

from pytest_mock import MockerFixture

from nefelibata.announcers.base import Announcer, Scope, get_announcers
from nefelibata.typing import Config

from ..conftest import MockEntryPoint


def make_dummy_announcer(class_name: str, scope: Scope) -> Type[Announcer]:
    """
    Make a dummy ``Announcer`` derived class.
    """
    return type(class_name, (Announcer,), {"scopes": [scope]})


def test_get_announcers(
    mocker: MockerFixture,
    make_entry_point: Type[MockEntryPoint],
    root: Path,
    config: Config,
) -> None:
    """
    Test ``get_announcers``.
    """
    DummyAnnouncer = make_dummy_announcer("DummyAnnouncer", Scope.SITE)
    entry_points = [
        make_entry_point("dummy_announcer", DummyAnnouncer),
    ]
    mocker.patch(
        "nefelibata.announcers.base.iter_entry_points",
        return_value=entry_points,
    )
    mocker.patch(
        "nefelibata.announcers.base.get_builders",
    )

    config = {
        "builders": {
            "site_builder": {
                "plugin": "site_builder",
                "home": "https://example.com/",
                "announce-on": ["dummy_announcer"],
            },
        },
        "announcers": {
            "dummy_announcer": {
                "plugin": "dummy_announcer",
            },
        },
    }
    announcers = get_announcers(root, config, Scope.SITE)
    assert len(announcers) == 1

    announcers = get_announcers(root, config, Scope.POST)
    assert len(announcers) == 0
