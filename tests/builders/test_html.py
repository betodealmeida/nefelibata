"""
Tests for ``nefelibata.builders.html``.
"""
# pylint: disable=invalid-name
from pathlib import Path
from typing import Any, Dict

import pytest
from freezegun import freeze_time
from pytest_mock import MockerFixture

from nefelibata import __version__
from nefelibata.builders.html import HTMLBuilder
from nefelibata.config import Config, SocialModel
from nefelibata.post import Post


@pytest.mark.asyncio
async def test_builder_setup(root: Path, config: Config) -> None:
    """
    Test that templates and build directory are created.
    """
    template_directory = root / "templates/builders/html/minimal/src"
    build_directory = root / "build/html"
    assert not template_directory.exists()
    assert not build_directory.exists()

    builder = HTMLBuilder(root, config, "https://example.com/")
    builder.setup()

    last_update: Dict[Any, Any] = {}
    assert template_directory.exists()
    for file in ("index.html", "atom.xml", "post.html"):
        assert (template_directory / file).exists()
        last_update[file] = (template_directory / file).stat().st_mtime
    assert build_directory.exists()
    last_update[build_directory] = build_directory.stat().st_mtime

    # on the second call the files and directories should be unmodified
    HTMLBuilder(root, config, "https://example.com/")
    for file in ("index.html", "atom.xml", "post.html"):
        assert (template_directory / file).stat().st_mtime == last_update[file]
    assert build_directory.stat().st_mtime == last_update[build_directory]


@pytest.mark.asyncio
async def test_builder_post(
    mocker: MockerFixture,
    root: Path,
    config: Config,
    post: Post,
) -> None:
    """
    Test ``process_post``.
    """
    _logger = mocker.patch("nefelibata.builders.base._logger")

    builder = HTMLBuilder(root, config, "https://example.com/")
    builder.setup()

    # call twice to check that it won't fail (shouldn't overwrite)
    builder.setup()

    with freeze_time("2021-01-02T00:00:00Z"):
        await builder.process_post(post)

    post_path = root / "build/html/first/index.html"

    # test that file was created
    assert post_path.exists()
    _logger.info.assert_called_with("Creating %s post", "HTML")
    with open(post_path, encoding="utf-8") as input_:
        content = input_.read()
    assert (
        content
        == f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="generator" content="Nefelibata {__version__}">
    <meta name="robots" content="index, follow">
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="description" content="Musings about the path and other things">

    <title>道&amp;c.: This is your first post</title>

    <link rel="canonical" href="https://example.com/" />
    <link rel="alternate" type="application/atom+xml" href="https://example.com/atom.xml" />
    <link rel="webmention" href="https://webmention.io/example.com/webmention" />
    <link rel="me" href="mailto:roberto@dealmeida.net" />

    <link rel="stylesheet" href="https://example.com/css/awsm_theme_big-stone.min.css" media="(prefers-color-scheme: dark)">
    <link rel="stylesheet" href="https://example.com/css/awsm_theme_pearl-lusta.min.css" media="(prefers-color-scheme: no-preference), (prefers-color-scheme: light)">
    <link rel="stylesheet" href="https://example.com/css/custom.css">
  </head>
  <body>
    <main>
      <nav>
        <ul>
          <li><a href="https://example.com/">Main index</a></li>
        </ul>
      </nav>

      <article class="h-entry">
        <h1 class="p-name">This is your first post</h1>

        <p>Published by <a class="p-author h-card" href="https://taoetc.org/">Beto Dealmeida</a>
        on <time class="dt-published" datetime="2020-12-31T16:00:00-08:00">2020-12-31 16:00:00-08:00</time></p>

        <p class="p-summary"><small>Hello, world!</small></p>

        <div class="e-content">
          <h1>Welcome</h1>
<p>This is your first post. It should be written using Markdown.</p>
<p>Read more about <a href="https://nefelibata.readthedocs.io/">Nefelibata</a>.</p>

        </div>


        <h2>Tags</h2>

        <ul>
          <li><a class="p-category" href="https://example.com/tags/blog.html">blog</a></li>
          <li><a class="p-category" href="https://example.com/tags/welcome.html">welcome</a></li>
        </ul>

        <h2>Categories</h2>

        <ul>
          <li><a class="p-category" href="https://example.com/categories/stem.html">STEM</a></li>
        </ul>

      </article>
    </main>
  </body>
</html>"""
    )

    # call again, test that file is up-to-date
    _logger.reset_mock()
    last_update = post_path.stat().st_mtime
    with freeze_time("2021-01-03T00:00:00Z"):
        await builder.process_post(post)
    assert post_path.stat().st_mtime == last_update
    _logger.debug.assert_called_with("Post %s is up-to-date, nothing to do", post_path)

    # call again, forcing a rebuild
    _logger.reset_mock()
    last_update = post_path.stat().st_mtime
    with freeze_time("2021-01-04T00:00:00Z"):
        await builder.process_post(post, force=True)
    assert post_path.stat().st_mtime > last_update
    _logger.info.assert_called_with("Creating %s post", "HTML")


@pytest.mark.asyncio
async def test_builder_site(
    mocker: MockerFixture,
    root: Path,
    config: Config,
    post: Post,
) -> None:
    """
    Test ``process_site``.
    """
    _logger = mocker.patch("nefelibata.builders.base._logger")
    mocker.patch("nefelibata.builders.base.get_posts", return_value=[post])

    config.social = [SocialModel(title="Mastodon", url="https://2c.taoetc.org/@beto")]
    builder = HTMLBuilder(root, config, "https://example.com/")
    builder.setup()

    with freeze_time("2021-01-02T00:00:00Z"):
        await builder.process_site()

    assets_directory = root / "build/html"
    assets = (
        "index.html",
        "atom.xml",
        "tags/welcome.html",
        "tags/blog.html",
        "categories/stem.html",
    )

    # test that files were created
    last_update: Dict[Any, Any] = {}
    for asset in assets:
        assert (assets_directory / asset).exists()
        last_update[asset] = (assets_directory / asset).stat().st_mtime
    _logger.info.assert_has_calls(
        [
            mocker.call("Creating %s", Path("/path/to/blog/build/html/index.html")),
            mocker.call("Creating %s", Path("/path/to/blog/build/html/atom.xml")),
            mocker.call(
                "Creating %s",
                Path("/path/to/blog/build/html/tags/blog.html"),
            ),
            mocker.call(
                "Creating %s",
                Path("/path/to/blog/build/html/tags/welcome.html"),
            ),
            mocker.call(
                "Creating %s",
                Path("/path/to/blog/build/html/categories/stem.html"),
            ),
        ],
    )
    with open(assets_directory / "index.html", encoding="utf-8") as input_:
        content = input_.read()
    assert (
        content
        == f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="generator" content="Nefelibata {__version__}">
    <meta name="robots" content="index, follow">
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="description" content="Musings about the path and other things">

    <title>道&amp;c.: Musings about the path and other things</title>

    <link rel="canonical" href="https://example.com/" />
    <link rel="alternate" type="application/atom+xml" href="https://example.com/atom.xml" />
    <link rel="webmention" href="https://webmention.io/example.com/webmention" />
    <link rel="me" href="mailto:roberto@dealmeida.net" />

    <link rel="stylesheet" href="https://example.com/css/awsm_theme_big-stone.min.css" media="(prefers-color-scheme: dark)">
    <link rel="stylesheet" href="https://example.com/css/awsm_theme_pearl-lusta.min.css" media="(prefers-color-scheme: no-preference), (prefers-color-scheme: light)">
    <link rel="stylesheet" href="https://example.com/css/custom.css">
  </head>
  <body>
    <main>
      <h1>道&amp;c.: Musings about the path and other things</h1>

      <h2 class="h-feed">Posts</h2>

      <ul>
        <li class="h-entry"><a class="p-name" href="https://example.com/first/index.html">This is your first post</a> </li>
      </ul>

      <h2>Links</h2>

      <ul>
        <li><a href="https://2c.taoetc.org/@beto" rel="me">Mastodon</a></li>
      </ul>

      <footer>
        <p>Crafted with ❤️ using <a href="https://nefelibata.readthedocs.io/">Nefelibata</a>.</p>
      </footer>
    </main>
  </body>
</html>"""
    )
    with open(assets_directory / "atom.xml", encoding="utf-8") as input_:
        content = input_.read()
    assert (
        content
        == """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <title>道&amp;c.</title>
    <link rel="self" type="application/atom+xml" href="https://example.com/atom.xml" />
    <id>https://example.com/</id>
    <updated>2020-12-31T16:04:00Z</updated>
<entry>
    <title>This is your first post</title>
    <link rel="alternate" type="text/html" href="https://example.com/first/index.html" />
    <id>tag:example.com,2020-12-31:first/index.html</id>
    <updated>2020-12-31T16:04:00Z</updated>
    <summary type="html">
        Hello, world!
        &lt;p&gt;&lt;a href="https://example.com/first/index.html"&gt;Permalink&lt;/p&gt;
    </summary>
    <author>
        <name>Beto Dealmeida</name>
        <email>roberto@dealmeida.net</email>
    </author>
    <category term="stem" />
    <content type="html">
        &lt;h1&gt;Welcome&lt;/h1&gt;
&lt;p&gt;This is your first post. It should be written using Markdown.&lt;/p&gt;
&lt;p&gt;Read more about &lt;a href=&#34;https://nefelibata.readthedocs.io/&#34;&gt;Nefelibata&lt;/a&gt;.&lt;/p&gt;

        &lt;p&gt;&lt;a href="https://example.com/first/index.html"&gt;Permalink&lt;/p&gt;
    </content>
</entry>
</feed>"""
    )

    # call again, test that file is up-to-date
    _logger.reset_mock()
    with freeze_time("2021-01-03T00:00:00Z"):
        await builder.process_site()
    for asset in assets:
        assert (assets_directory / asset).stat().st_mtime == last_update[asset]
    _logger.debug.assert_has_calls(
        [
            mocker.call(
                "File %s is up-to-date, nothing to do",
                Path("/path/to/blog/build/html/index.html"),
            ),
            mocker.call(
                "File %s is up-to-date, nothing to do",
                Path("/path/to/blog/build/html/atom.xml"),
            ),
            mocker.call(
                "File %s is up-to-date, nothing to do",
                Path("/path/to/blog/build/html/tags/blog.html"),
            ),
            mocker.call(
                "File %s is up-to-date, nothing to do",
                Path("/path/to/blog/build/html/tags/welcome.html"),
            ),
            mocker.call(
                "File %s is up-to-date, nothing to do",
                Path("/path/to/blog/build/html/categories/stem.html"),
            ),
        ],
    )

    # call again, forcing a rebuild
    _logger.reset_mock()
    with freeze_time("2021-01-04T00:00:00Z"):
        await builder.process_site(force=True)
    for asset in assets:
        assert (assets_directory / asset).stat().st_mtime > last_update[asset]
    _logger.info.assert_has_calls(
        [
            mocker.call("Creating %s", Path("/path/to/blog/build/html/index.html")),
            mocker.call("Creating %s", Path("/path/to/blog/build/html/atom.xml")),
            mocker.call(
                "Creating %s",
                Path("/path/to/blog/build/html/tags/blog.html"),
            ),
            mocker.call(
                "Creating %s",
                Path("/path/to/blog/build/html/tags/welcome.html"),
            ),
            mocker.call(
                "Creating %s",
                Path("/path/to/blog/build/html/categories/stem.html"),
            ),
        ],
    )
