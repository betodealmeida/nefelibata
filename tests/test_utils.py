from pathlib import Path

from nefelibata import config_filename
from nefelibata.utils import get_config

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
theme: pure-blog
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
        "theme": "pure-blog",
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
theme: pure-blog
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
        "theme": "pure-blog",
        "language": "en",
    }
