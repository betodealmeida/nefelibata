import logging
from pathlib import Path

import pytest
from nefelibata import config_filename
from nefelibata.utils import find_directory
from nefelibata.utils import get_config
from nefelibata.utils import sanitize
from nefelibata.utils import setup_logging

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


def test_get_config(fs):
    root = Path("/path/to/blog")
    fs.create_dir(root)

    contents = """
title: Tao etc.
subtitle: Musings about the path and other things
author:
    name: Beto Dealmeida
    email: roberto@dealmeida.net
    profile_picture: http://www.gravatar.com/avatar/58b573d3eac03131faee739dfc7b360a
url: http://blog.taoetc.org/  # slashing trail is important
posts-to-show: 5
theme: test-theme
language: en
    """
    with open(root / config_filename, "w") as fp:
        fp.write(contents)

    config = get_config(root)
    assert config == {
        "title": "Tao etc.",
        "subtitle": "Musings about the path and other things",
        "author": {
            "name": "Beto Dealmeida",
            "email": "roberto@dealmeida.net",
            "profile_picture": "http://www.gravatar.com/avatar/58b573d3eac03131faee739dfc7b360a",
        },
        "url": "http://blog.taoetc.org/",
        "posts-to-show": 5,
        "theme": "test-theme",
        "language": "en",
    }


def test_get_config_no_profile_picture(fs):
    root = Path("/path/to/blog")
    fs.create_dir(root)

    contents = """
title: Tao etc.
subtitle: Musings about the path and other things
author:
    name: Beto Dealmeida
    email: roberto@dealmeida.net
url: http://blog.taoetc.org/  # slashing trail is important
posts-to-show: 5
theme: test-theme
language: en
    """
    with open(root / config_filename, "w") as fp:
        fp.write(contents)

    config = get_config(root)
    assert config == {
        "title": "Tao etc.",
        "subtitle": "Musings about the path and other things",
        "author": {
            "name": "Beto Dealmeida",
            "email": "roberto@dealmeida.net",
            "profile_picture": "http://www.gravatar.com/avatar/58b573d3eac03131faee739dfc7b360a",
        },
        "url": "http://blog.taoetc.org/",
        "posts-to-show": 5,
        "theme": "test-theme",
        "language": "en",
    }


def test_setup_logging():
    setup_logging("debug")
    assert logging.root.level == logging.DEBUG


def test_setup_logging_invalid():
    with pytest.raises(ValueError) as excinfo:
        setup_logging("invalid")

    assert str(excinfo.value) == "Invalid log level: invalid"


def test_find_directory(fs):
    fs.create_dir("/path/to/blog/posts/first/css")
    fs.create_file("/path/to/blog/nefelibata.yaml")

    path = find_directory(Path("/path/to/blog/posts/first/css"))
    assert path == Path("/path/to/blog")

    with pytest.raises(SystemExit) as excinfo:
        find_directory(Path("/path/to"))

    assert str(excinfo.value) == "No configuration found!"


def test_sanitize():
    assert sanitize("Hello, World!") == "hello_world"
    assert sanitize("Olá, mundo!") == "ola_mundo"
