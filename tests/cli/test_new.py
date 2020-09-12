from pathlib import Path
from unittest.mock import MagicMock

import pytest
from nefelibata.cli.new import run

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


def test_run(monkeypatch, fs):
    monkeypatch.setenv("EDITOR", "")

    root = Path("/path/to/blog")
    fs.create_dir(root / "posts")
    directory = "first_post"

    run(root, directory)

    for resource in ["css", "js", "img", "index.mkd"]:
        assert (root / "posts" / directory / resource).exists()


def test_run_no_overwrite(monkeypatch, fs):
    monkeypatch.setenv("EDITOR", "")

    root = Path("/path/to/blog")
    fs.create_dir(root / "posts")
    directory = "first_post"
    fs.create_dir(root / "posts" / directory)

    with pytest.raises(IOError) as excinfo:
        run(root, directory)

    assert str(excinfo.value) == "Directory already exists!"


def test_run_call_editor(mocker, monkeypatch, fs):
    monkeypatch.setenv("EDITOR", "vim")
    mock_call = MagicMock()
    mocker.patch("nefelibata.cli.new.call", mock_call)

    root = Path("/path/to/blog")
    fs.create_dir(root / "posts")
    directory = "first_post"

    run(root, directory)

    mock_call.assert_called_with(["vim", root / "posts" / directory / "index.mkd"])


def test_custom_template(monkeypatch, fs):
    monkeypatch.setenv("EDITOR", "")

    root = Path("/path/to/blog")
    fs.create_dir(root / "posts")
    directory = "first_post"

    with open(root / "nefelibata.yaml", "w") as fp:
        fp.write(
            """
author:
    name: John Doe
    profile_picture: https://example.com/picture.jpg

templates:
    book:
        - title
        - rating
            """,
        )

    run(root, directory, "book")

    with open(root / "posts" / directory / "index.mkd") as fp:
        content = fp.read()

    assert content == (
        """subject: first_post
summary: 
keywords: 
type: book
book-title: 
book-rating: 


"""  # noqa: W291
    )


def test_invalid_template(monkeypatch, fs):
    monkeypatch.setenv("EDITOR", "")

    root = Path("/path/to/blog")
    fs.create_dir(root / "posts")
    directory = "first_post"

    with open(root / "nefelibata.yaml", "w") as fp:
        fp.write(
            """
author:
    name: John Doe
    profile_picture: https://example.com/picture.jpg
            """,
        )

    with pytest.raises(Exception) as excinfo:
        run(root, directory, "book")

    assert str(excinfo.value) == "Invalid post type: book"
