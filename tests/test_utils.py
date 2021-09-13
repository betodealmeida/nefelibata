"""
Tests for ``nefelibata.utils``.
"""
# pylint: disable=invalid-name

import logging
from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from nefelibata.typing import Config
from nefelibata.utils import find_directory, get_config, setup_logging


def test_setup_logging() -> None:
    """
    Test ``setup_logging``.
    """
    setup_logging("debug")
    assert logging.root.level == logging.DEBUG

    with pytest.raises(ValueError) as excinfo:
        setup_logging("invalid")
    assert str(excinfo.value) == "Invalid log level: invalid"


def test_find_directory(fs: FakeFilesystem) -> None:
    """
    Test ``find_directory``.
    """
    fs.create_dir("/path/to/blog/posts/first/css")
    fs.create_file("/path/to/blog/nefelibata.yaml")

    path = find_directory(Path("/path/to/blog/posts/first/css"))
    assert path == Path("/path/to/blog")

    with pytest.raises(SystemExit) as excinfo:
        find_directory(Path("/path/to"))
    assert str(excinfo.value) == "No configuration found!"


def test_get_config(root: Path, config: Config) -> None:
    """
    Test ``get_config``.
    """
    config = get_config(root)
    assert config == {
        "title": "道&c.",
        "subtitle": "Musings about the path and other things",
        "author": {
            "name": "Beto Dealmeida",
            "url": "https://taoetc.org/",
            "email": "roberto@dealmeida.net",
            "note": "Este, sou eu",
        },
        "language": "en",
        "categories": {
            "stem": {
                "label": "STEM",
                "description": "Science, technology, engineering, & math",
                "tags": ["blog", "programming"],
            },
        },
    }

    with pytest.raises(SystemExit) as excinfo:
        get_config(Path("/path/to"))
    assert str(excinfo.value) == "No configuration found!"
