from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import List
from unittest.mock import MagicMock

import dateutil.parser
import pytest
from freezegun import freeze_time
from nefelibata.builders.tags import TagsBuilder
from nefelibata.post import Post

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


test_template = """
{{ breadcrumbs[1][0] }}
{%- for post in posts %}
{{ post.title }}
{% endfor -%}
{{ next }}
"""


class MockPost:
    def __init__(self, title: str, date: str, tags: List[str]):
        self.title = title
        self.date = date
        self.parsed = {"keywords": ", ".join(tags)}

        mock_file_path = MagicMock()
        mock_file_path.stat.return_value.st_mtime = dateutil.parser.parse(
            date,
        ).timestamp()
        self.file_path = mock_file_path


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
    fs.create_dir(root / "templates/test-theme")
    with open(root / "templates/test-theme/index.html", "w") as fp:
        fp.write(test_template)

    builder = TagsBuilder(root, config)

    posts = [
        MockPost("one", "2020-01-01", ["a", "b", "d"]),
        MockPost("two", "2020-01-02", ["b", "c", "d"]),
        MockPost("three", "2020-01-03", ["a", "c", "d"]),
    ]
    mocker.patch("nefelibata.builders.tags.get_posts", return_value=posts)
    with freeze_time("2020-01-04"):
        builder.process_site()

    assert (root / "build/a.html").exists()
    assert (root / "build/b.html").exists()
    assert (root / "build/c.html").exists()
    assert (root / "build/d.html").exists()
    assert (root / "build/d1.html").exists()

    with open(root / "build/a.html") as fp:
        contents = fp.read()
    assert contents == '\nPosts tagged "a"\nthree\n\none\nNone'

    with open(root / "build/b.html") as fp:
        contents = fp.read()
    assert contents == '\nPosts tagged "b"\ntwo\n\none\nNone'

    with open(root / "build/c.html") as fp:
        contents = fp.read()
    assert contents == '\nPosts tagged "c"\nthree\n\ntwo\nNone'

    with open(root / "build/d.html") as fp:
        contents = fp.read()
    assert contents == '\nPosts tagged "d"\nthree\n\ntwo\nd1.html'

    with open(root / "build/d1.html") as fp:
        contents = fp.read()
    assert contents == '\nPosts tagged "d"\none\nNone'

    # check that only tags with updated posts get rebuild
    posts = [
        MockPost("one", "2020-01-05", ["a", "b", "d"]),
        MockPost("two", "2020-01-02", ["b", "c", "d"]),
        MockPost("three", "2020-01-03", ["a", "c", "d"]),
    ]
    mocker.patch("nefelibata.builders.tags.get_posts", return_value=posts)
    with freeze_time("2020-01-06"):
        builder.process_site()

    assert datetime.fromtimestamp((root / "build/a.html").stat().st_mtime).astimezone(
        timezone.utc,
    ) == datetime(2020, 1, 6, 0, 0, tzinfo=timezone.utc)
    assert datetime.fromtimestamp((root / "build/b.html").stat().st_mtime).astimezone(
        timezone.utc,
    ) == datetime(2020, 1, 6, 0, 0, tzinfo=timezone.utc)
    assert datetime.fromtimestamp((root / "build/c.html").stat().st_mtime).astimezone(
        timezone.utc,
    ) == datetime(2020, 1, 4, 0, 0, tzinfo=timezone.utc)
    assert datetime.fromtimestamp((root / "build/d.html").stat().st_mtime).astimezone(
        timezone.utc,
    ) == datetime(2020, 1, 6, 0, 0, tzinfo=timezone.utc)
