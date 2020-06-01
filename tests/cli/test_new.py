from pathlib import Path
from unittest.mock import MagicMock

import pytest
from nefelibata.cli.new import run

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


def test_run(mocker, monkeypatch, fs):
    monkeypatch.setenv("EDITOR", "")

    root = Path("/path/to/blog")
    fs.create_dir(root / "posts")
    directory = "first_post"

    run(root, directory)

    for resource in ["css", "js", "img", "index.mkd"]:
        assert (root / "posts" / directory / resource).exists()


def test_run_no_overwrite(mocker, monkeypatch, fs):
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
