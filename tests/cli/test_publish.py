from pathlib import Path
from unittest.mock import call
from unittest.mock import MagicMock

import pytest
from nefelibata.cli.publish import run
from nefelibata.post import Post

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


config = {
    "theme": "test-theme",
    "announce-on": ["announcer1", "announcer2"],
}


def test_run(mocker, fs):
    root = Path("/path/to/blog")
    fs.create_dir(root)

    # create a couple posts
    fs.create_file(root / "posts/one/index.mkd")
    fs.create_dir(root / "posts/two")
    with open(root / "posts/two/index.mkd", "w") as fp:
        fp.write("subject: Hello!\nannounce-on: announcer1\n")
    post1 = Post(root / "posts/one/index.mkd")
    post2 = Post(root / "posts/two/index.mkd")
    mocker.patch(
        "nefelibata.cli.publish.get_posts", return_value=[post1, post2],
    )

    # mock config
    mocker.patch("nefelibata.cli.publish.get_config", return_value=config)

    # mock publishers
    Publisher1 = MagicMock()
    Publisher2 = MagicMock()
    mocker.patch(
        "nefelibata.cli.publish.get_publishers", return_value=[Publisher1, Publisher2],
    )

    # mock announcers
    Announcer1 = MagicMock()
    Announcer1.match.side_effect = [True, False]
    Announcer2 = MagicMock()
    mocker.patch(
        "nefelibata.cli.publish.get_announcers", return_value=[Announcer1, Announcer2],
    )

    run(root)

    Publisher1.publish.assert_called_with(False)
    Publisher2.publish.assert_called_with(False)
    Announcer1.update_links.assert_has_calls([call(post1)])
    Announcer2.update_links.assert_has_calls([call(post1), call(post2)])
