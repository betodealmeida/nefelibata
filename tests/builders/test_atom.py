from pathlib import Path

import pytest
from nefelibata.builders.atom import AtomBuilder
from nefelibata.post import Post

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


test_template = """
{%- for post in posts -%}
{{ post.title }}
{% endfor -%}
"""


class MockPost:
    def __init__(self, title: str, date: str):
        self.title = title
        self.date = date


def test_process_site(mocker, fs):
    config = {
        "url": "https://blog.example.com/",
        "language": "en",
        "theme": "test-theme",
        "posts-to-show": 2,
    }

    root = Path("/path/to/blog")
    fs.create_dir(root)
    fs.create_dir(root / "build")
    fs.create_dir(root / "templates")
    with open(root / "templates/atom.xml", "w") as fp:
        fp.write(test_template)

    posts = [
        MockPost("one", "2020-01-01"),
        MockPost("two", "2020-01-02"),
        MockPost("three", "2020-01-03"),
    ]
    mocker.patch("nefelibata.builders.atom.get_posts", return_value=posts)

    builder = AtomBuilder(root, config)
    builder.process_site()

    assert (root / "build/atom.xml").exists()

    with open(root / "build/atom.xml") as fp:
        contents = fp.read()
    assert contents == "three\ntwo\n"
