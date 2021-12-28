"""
Test ``nefelibata.cli.new``.
"""
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from nefelibata.cli import new
from nefelibata.config import Config


@pytest.mark.asyncio
async def test_run(
    monkeypatch: pytest.MonkeyPatch,
    root: Path,
) -> None:
    """
    Test ``new``.
    """
    monkeypatch.setenv("EDITOR", "")

    await new.run(root, "A new post")

    filepath = root / "posts/a_new_post/index.mkd"
    with open(filepath, encoding="utf-8") as input_:
        content = input_.read()
    assert content == "subject: A new post\nsummary: \nkeywords: \n\n\n"

    with pytest.raises(IOError) as excinfo:
        await new.run(root, "A new post")
    assert str(excinfo.value) == "Directory already exists!"


@pytest.mark.asyncio
async def test_run_with_editor(
    monkeypatch: pytest.MonkeyPatch,
    mocker: MockerFixture,
    root: Path,
) -> None:
    """
    Test that the editor will be called if set.
    """
    monkeypatch.setenv("EDITOR", "vim")
    call = mocker.patch("nefelibata.cli.new.call")

    await new.run(root, "A new post")

    call.assert_called_with(["vim", root / "posts/a_new_post/index.mkd"])


@pytest.mark.asyncio
async def test_run_with_type(
    monkeypatch: pytest.MonkeyPatch,
    mocker: MockerFixture,
    root: Path,
    config: Config,
) -> None:
    """
    Test creating a new post with a valid type.
    """
    monkeypatch.setenv("EDITOR", "")
    config.templates = {
        "book": ["title", "author"],
    }
    mocker.patch("nefelibata.cli.new.get_config", return_value=config)

    await new.run(root, "A book I liked", "book")

    filepath = root / "posts/a_book_i_liked/index.mkd"
    with open(filepath, encoding="utf-8") as input_:
        content = input_.read()
    assert content == (
        "subject: A book I liked\n"
        "summary: \n"
        "keywords: \n"
        "type: book\n"
        "book-title: \n"
        "book-author: \n"
        "\n\n"
    )


@pytest.mark.asyncio
async def test_run_with_invalid_type(
    monkeypatch: pytest.MonkeyPatch,
    root: Path,
    config: Config,  # pylint: disable=unused-argument
) -> None:
    """
    Test creating a new post with an invalid type.
    """
    monkeypatch.setenv("EDITOR", "")

    with pytest.raises(Exception) as excinfo:
        await new.run(root, "A book I liked", "book")
    assert str(excinfo.value) == "Invalid post type: book"
