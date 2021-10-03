"""
Tests for ``nefelibata.announcers.base``.
"""

from pathlib import Path
from typing import List, Type

import pytest
from pytest_mock import MockerFixture

from nefelibata.announcers.base import Announcer, Scope, get_announcers
from nefelibata.config import AnnouncerModel, BuilderModel, Config
from nefelibata.post import Post

from ..conftest import MockEntryPoint


def make_dummy_announcer(class_name: str, scopes: List[Scope]) -> Type[Announcer]:
    """
    Make a dummy ``Announcer`` derived class.
    """
    return type(class_name, (Announcer,), {"scopes": scopes})


@pytest.mark.asyncio
async def test_announcer(root: Path, config: Config, post: Post) -> None:
    """
    Test the base announcer methods.
    """
    announcer = Announcer(root, config, [])

    assert (await announcer.announce_post(post)) is None
    assert (await announcer.announce_site()) is None
    assert (await announcer.collect_post(post)) == {}
    assert (await announcer.collect_site()) == {}


def test_get_announcers(
    mocker: MockerFixture,
    make_entry_point: Type[MockEntryPoint],
    root: Path,
    config: Config,
) -> None:
    """
    Test ``get_announcers``.
    """
    DummyAnnouncer = make_dummy_announcer("DummyAnnouncer", [Scope.SITE])
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

    config.builders = {
        "site_builder": BuilderModel(
            **{
                "plugin": "site_builder",
                "announce-on": ["dummy_announcer"],
                "publish-to": [],
                "home": "https://example.com/",
                "path": "generic",
            }
        ),
    }
    config.announcers = {
        "dummy_announcer": AnnouncerModel(
            **{
                "plugin": "dummy_announcer",
            }
        ),
    }
    announcers = get_announcers(root, config, Scope.SITE)
    assert len(announcers) == 1

    announcers = get_announcers(root, config, Scope.POST)
    assert len(announcers) == 0
