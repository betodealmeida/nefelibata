from pathlib import Path
from unittest.mock import call
from unittest.mock import MagicMock

import pytest
from nefelibata.cli.build import run
from nefelibata.post import Post

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


config = {
    "theme": "test-theme",
    "builders": ["post", "index", "tags", "atom"],
    "announce-on": ["announcer1", "announcer2"],
}


def test_run(mocker, fs):
    root = Path("/path/to/blog")
    fs.create_dir(root)

    # create a couple posts
    fs.create_file(root / "posts/one/index.mkd")
    fs.create_file(root / "posts/two/index.mkd")
    post1 = Post(root / "posts/one/index.mkd")
    post2 = Post(root / "posts/two/index.mkd")
    mocker.patch(
        "nefelibata.cli.build.get_posts", return_value=[post1, post2],
    )

    # mock config
    mocker.patch("nefelibata.cli.build.get_config", return_value=config)

    # mock builders
    PostBuilder = MagicMock()
    SiteBuilder = MagicMock()
    PostSiteBuilder = MagicMock()
    mocker.patch(
        "nefelibata.cli.build.get_builders",
        side_effect=[[PostBuilder, PostSiteBuilder], [SiteBuilder, PostSiteBuilder]],
    )

    # mock assistants
    PostAssistant = MagicMock()
    SiteAssistant = MagicMock()
    PostSiteAssistant = MagicMock()
    mocker.patch(
        "nefelibata.cli.build.get_assistants",
        side_effect=[
            [PostAssistant, PostSiteAssistant],
            [SiteAssistant, PostSiteAssistant],
        ],
    )

    # mock announcers
    Announcer1 = MagicMock()
    Announcer1.match.side_effect = [True, False]  # match only post1
    Announcer2 = MagicMock()
    mocker.patch(
        "nefelibata.cli.build.get_announcers", return_value=[Announcer1, Announcer2],
    )

    run(root)

    PostBuilder.process_post.assert_has_calls([call(post1, False), call(post2, False)])
    PostSiteBuilder.process_post.assert_has_calls(
        [call(post1, False), call(post2, False)],
    )
    PostAssistant.process_post.assert_has_calls(
        [call(post1, False), call(post2, False)],
    )
    PostSiteAssistant.process_post.assert_has_calls(
        [call(post1, False), call(post2, False)],
    )
    Announcer1.update_replies.assert_has_calls([call(post1)])
    Announcer2.update_replies.assert_has_calls([call(post1), call(post2)])
    SiteBuilder.process_site.assert_has_calls([call(False)])
    PostSiteBuilder.process_site.assert_has_calls([call(False)])
    SiteAssistant.process_site.assert_has_calls([call(False)])
    PostSiteAssistant.process_site.assert_has_calls([call(False)])


def test_run_build_exists(mocker, fs):
    root = Path("/path/to/blog")
    fs.create_dir(root)
    fs.create_dir(root / "build")

    # create some files in the theme
    fs.create_file(root / "templates/test-theme/css/test.css")

    # create a couple posts
    fs.create_file(root / "posts/one/index.mkd")
    fs.create_file(root / "posts/two/index.mkd")
    post1 = Post(root / "posts/one/index.mkd")
    post2 = Post(root / "posts/two/index.mkd")
    mocker.patch(
        "nefelibata.cli.build.get_posts", return_value=[post1, post2],
    )

    # mock config
    mocker.patch("nefelibata.cli.build.get_config", return_value=config)

    # mock builders
    PostBuilder = MagicMock()
    SiteBuilder = MagicMock()
    PostSiteBuilder = MagicMock()
    mocker.patch(
        "nefelibata.cli.build.get_builders",
        side_effect=[[PostBuilder, PostSiteBuilder], [SiteBuilder, PostSiteBuilder]],
    )

    # mock assistants
    PostAssistant = MagicMock()
    SiteAssistant = MagicMock()
    PostSiteAssistant = MagicMock()
    mocker.patch(
        "nefelibata.cli.build.get_assistants",
        side_effect=[
            [PostAssistant, PostSiteAssistant],
            [SiteAssistant, PostSiteAssistant],
        ],
    )

    # mock announcers
    Announcer1 = MagicMock()
    Announcer2 = MagicMock()
    mocker.patch(
        "nefelibata.cli.build.get_announcers", return_value=[Announcer1, Announcer2],
    )

    run(root)

    assert (root / "build/css/test.css").exists()


def test_run_no_collect_replies(mocker, fs):
    root = Path("/path/to/blog")
    fs.create_dir(root)
    fs.create_dir(root / "build")

    # create some files in the theme
    fs.create_file(root / "templates/test-theme/css/test.css")

    # create a couple posts
    fs.create_file(root / "posts/one/index.mkd")
    fs.create_file(root / "posts/two/index.mkd")
    post1 = Post(root / "posts/one/index.mkd")
    post2 = Post(root / "posts/two/index.mkd")
    mocker.patch(
        "nefelibata.cli.build.get_posts", return_value=[post1, post2],
    )

    # mock config
    mocker.patch("nefelibata.cli.build.get_config", return_value=config)

    # mock builders
    PostBuilder = MagicMock()
    SiteBuilder = MagicMock()
    PostSiteBuilder = MagicMock()
    mocker.patch(
        "nefelibata.cli.build.get_builders",
        side_effect=[[PostBuilder, PostSiteBuilder], [SiteBuilder, PostSiteBuilder]],
    )

    # mock assistants
    PostAssistant = MagicMock()
    SiteAssistant = MagicMock()
    PostSiteAssistant = MagicMock()
    mocker.patch(
        "nefelibata.cli.build.get_assistants",
        side_effect=[
            [PostAssistant, PostSiteAssistant],
            [SiteAssistant, PostSiteAssistant],
        ],
    )

    # mock announcers
    Announcer1 = MagicMock()
    Announcer2 = MagicMock()
    mocker.patch(
        "nefelibata.cli.build.get_announcers", return_value=[Announcer1, Announcer2],
    )

    run(root, collect_replies=False)

    Announcer1.update_replies.assert_not_called()
    Announcer2.update_replies.assert_not_called()


def test_run_post_up_to_date(mocker, fs):
    root = Path("/path/to/blog")
    fs.create_dir(root)
    fs.create_dir(root / "build")

    # create some files in the theme
    fs.create_file(root / "templates/test-theme/css/test.css")

    # create a couple posts
    fs.create_file(root / "posts/one/index.mkd")
    fs.create_file(root / "posts/two/index.mkd")
    post1 = Post(root / "posts/one/index.mkd")
    post2 = Post(root / "posts/two/index.mkd")
    mocker.patch(
        "nefelibata.cli.build.get_posts", return_value=[post1, post2],
    )

    # mock config
    mocker.patch("nefelibata.cli.build.get_config", return_value=config)

    # mock builders
    PostBuilder = MagicMock()
    SiteBuilder = MagicMock()
    PostSiteBuilder = MagicMock()
    mocker.patch(
        "nefelibata.cli.build.get_builders",
        side_effect=[[PostBuilder, PostSiteBuilder], [SiteBuilder, PostSiteBuilder]],
    )

    # mock assistants
    PostAssistant = MagicMock()
    SiteAssistant = MagicMock()
    PostSiteAssistant = MagicMock()
    mocker.patch(
        "nefelibata.cli.build.get_assistants",
        side_effect=[
            [PostAssistant, PostSiteAssistant],
            [SiteAssistant, PostSiteAssistant],
        ],
    )

    # mock announcers
    Announcer1 = MagicMock()
    Announcer2 = MagicMock()
    mocker.patch(
        "nefelibata.cli.build.get_announcers", return_value=[Announcer1, Announcer2],
    )

    # make sure one of the posts is up-to-date
    fs.create_file(root / "posts/one/index.html")

    run(root)

    PostBuilder.process_post.assert_has_calls([call(post2, False)])
    PostSiteBuilder.process_post.assert_has_calls([call(post2, False)])
    PostAssistant.process_post.assert_has_calls([call(post2, False)])
    PostSiteAssistant.process_post.assert_has_calls([call(post2, False)])
    Announcer1.update_replies.assert_has_calls([call(post2)])
    Announcer2.update_replies.assert_has_calls([call(post2)])


def test_run_skip_symlink(mocker, fs):
    root = Path("/path/to/blog")
    fs.create_dir(root)

    # create a first post
    fs.create_file(root / "posts/one/index.mkd")
    post1 = Post(root / "posts/one/index.mkd")
    mocker.patch(
        "nefelibata.cli.build.get_posts", return_value=[post1],
    )

    # mock config
    mocker.patch("nefelibata.cli.build.get_config", return_value=config)

    # mock builders
    PostBuilder = MagicMock()
    SiteBuilder = MagicMock()
    PostSiteBuilder = MagicMock()
    mocker.patch(
        "nefelibata.cli.build.get_builders",
        side_effect=[
            [PostBuilder, PostSiteBuilder],
            [SiteBuilder, PostSiteBuilder],
            [PostBuilder, PostSiteBuilder],
            [SiteBuilder, PostSiteBuilder],
        ],
    )

    # mock assistants
    PostAssistant = MagicMock()
    SiteAssistant = MagicMock()
    PostSiteAssistant = MagicMock()
    mocker.patch(
        "nefelibata.cli.build.get_assistants",
        side_effect=[
            [PostAssistant, PostSiteAssistant],
            [SiteAssistant, PostSiteAssistant],
            [PostAssistant, PostSiteAssistant],
            [SiteAssistant, PostSiteAssistant],
        ],
    )

    # mock announcers
    Announcer1 = MagicMock()
    Announcer2 = MagicMock()
    mocker.patch(
        "nefelibata.cli.build.get_announcers", return_value=[Announcer1, Announcer2],
    )

    run(root)

    # create a second post
    fs.create_file(root / "posts/two/index.mkd")
    post2 = Post(root / "posts/two/index.mkd")
    mocker.patch(
        "nefelibata.cli.build.get_posts", return_value=[post1, post2],
    )

    run(root)
