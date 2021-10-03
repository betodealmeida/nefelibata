"""
Tests for ``nefelibata.assistants.base``.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Type

import pytest
from freezegun import freeze_time
from pytest_mock import MockerFixture

from nefelibata.announcers.base import Scope
from nefelibata.assistants.base import Assistant, get_assistants
from nefelibata.config import AssistantModel, Config
from nefelibata.post import Post

from ..conftest import MockEntryPoint


def make_dummy_assistant(class_name: str, scopes: List[Scope]) -> Type[Assistant]:
    """
    Make a dummy ``Assistant`` derived class.
    """
    return type(class_name, (Assistant,), {"scopes": scopes})


@pytest.mark.asyncio
async def test_assistant(root: Path, config: Config, post: Post) -> None:
    """
    Test the base assistant methods.
    """

    assistant = Assistant(root, config)

    await assistant.process_post(post)
    assert not (post.path.parent / ".yaml").exists()
    assert (await assistant.get_post_metadata(post)) == {}

    await assistant.process_site()
    assert not (root / ".yaml").exists()
    assert (await assistant.get_site_metadata()) == {}


@pytest.mark.asyncio
async def test_assistant_dummy(root: Path, config: Config, post: Post) -> None:
    """
    Test a simple assistant.
    """

    class DummyAssistant(Assistant):
        """
        A dummy assistant.
        """

        name = "dummy"

        async def get_post_metadata(self, post: Post) -> Dict[str, Any]:
            return {"hello": "world"}

        async def get_site_metadata(self) -> Dict[str, Any]:
            return {"hello": "world"}

    assistant = DummyAssistant(root, config)

    with freeze_time("2021-01-01T00:00:00Z"):
        await assistant.process_post(post)
        await assistant.process_site()
    assert (post.path.parent / "dummy.yaml").stat().st_mtime == datetime(
        2021,
        1,
        1,
        0,
        0,
        tzinfo=timezone.utc,
    ).timestamp()
    assert (root / "dummy.yaml").stat().st_mtime == datetime(
        2021,
        1,
        1,
        0,
        0,
        tzinfo=timezone.utc,
    ).timestamp()

    with freeze_time("2021-01-02T00:00:00Z"):
        await assistant.process_post(post)
        await assistant.process_site()
    assert (post.path.parent / "dummy.yaml").stat().st_mtime == datetime(
        2021,
        1,
        1,
        0,
        0,
        tzinfo=timezone.utc,
    ).timestamp()
    assert (root / "dummy.yaml").stat().st_mtime == datetime(
        2021,
        1,
        1,
        0,
        0,
        tzinfo=timezone.utc,
    ).timestamp()

    with freeze_time("2021-01-03T00:00:00Z"):
        await assistant.process_post(post, force=True)
        await assistant.process_site(force=True)
    assert (post.path.parent / "dummy.yaml").stat().st_mtime == datetime(
        2021,
        1,
        3,
        0,
        0,
        tzinfo=timezone.utc,
    ).timestamp()
    assert (root / "dummy.yaml").stat().st_mtime == datetime(
        2021,
        1,
        3,
        0,
        0,
        tzinfo=timezone.utc,
    ).timestamp()


def test_get_assistants(
    mocker: MockerFixture,
    make_entry_point: Type[MockEntryPoint],
    root: Path,
    config: Config,
) -> None:
    """
    Test ``get_assistants``.
    """
    DummyAssistant = make_dummy_assistant("DummyAssistant", [Scope.SITE])
    entry_points = [
        make_entry_point("dummy_assistant", DummyAssistant),
    ]
    mocker.patch(
        "nefelibata.assistants.base.iter_entry_points",
        return_value=entry_points,
    )

    config.assistants = {
        "dummy_assistant": AssistantModel(
            **{
                "plugin": "dummy_assistant",
            }
        ),
    }
    assistants = get_assistants(root, config, Scope.SITE)
    assert len(assistants) == 1

    assistants = get_assistants(root, config, Scope.POST)
    assert len(assistants) == 0
