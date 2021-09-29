"""
Tests for ``nefelibata.utils``.
"""
# pylint: disable=invalid-name

import logging
from pathlib import Path

import pytest
from pydantic import BaseModel
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest_mock import MockerFixture

from nefelibata.announcers.base import Interaction
from nefelibata.typing import Config
from nefelibata.utils import (
    dict_merge,
    find_directory,
    get_config,
    load_yaml,
    setup_logging,
)


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


def test_load_yaml(mocker: MockerFixture, fs: FakeFilesystem) -> None:
    """
    Test ``load_yaml``.
    """
    assert load_yaml(Path("/path/to/blog/missing.yaml"), BaseModel) == {}

    fs.create_file(
        "/path/to/blog/existing.yaml",
        contents="""
reply,gemini://ew.srht.site/en/2021/20210915-re-changing-old-code-is-risky.gmi:
  id: reply,gemini://ew.srht.site/en/2021/20210915-re-changing-old-code-is-risky.gmi
  name: '2021-09-15 ~ew''s FlightLog: Re: Changing old code is risky'
  timestamp: null
  type: reply
  uri: gemini://ew.srht.site/en/2021/20210915-re-changing-old-code-is-risky.gmi
    """,
    )
    assert load_yaml(Path("/path/to/blog/existing.yaml"), Interaction) == {
        (
            "reply,gemini://ew.srht.site/en/2021/"
            "20210915-re-changing-old-code-is-risky.gmi"
        ): Interaction(
            id="reply,gemini://ew.srht.site/en/2021/20210915-re-changing-old-code-is-risky.gmi",
            name="2021-09-15 ~ew's FlightLog: Re: Changing old code is risky",
            uri="gemini://ew.srht.site/en/2021/20210915-re-changing-old-code-is-risky.gmi",
            type="reply",
            timestamp=None,
        ),
    }

    path = Path("/path/to/blog/invalid.yaml")
    fs.create_file(path, contents="[1,2,3")
    _logger = mocker.patch("nefelibata.utils._logger")
    assert load_yaml(path, BaseModel) == {}
    assert _logger.warning.called_with("Invalid YAML file: %s", path)


def test_dict_merge() -> None:
    """
    Test ``dict_merge``.
    """
    original = {"a": {"b": "c"}}
    update = {"d": {"e": "f"}, "a": {"g": "h"}}
    dict_merge(original, update)
    assert original == {"a": {"b": "c", "g": "h"}, "d": {"e": "f"}}
