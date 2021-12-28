"""
Tests for ``nefelibata.builders.gemini``.
"""
# pylint: disable=invalid-name
from pathlib import Path
from typing import Any, Dict

import pytest
from freezegun import freeze_time
from marko import Markdown
from pytest_mock import MockerFixture

from nefelibata.builders.gemini import GeminiBuilder, GeminiRenderer
from nefelibata.config import Config, SocialModel
from nefelibata.enclosure import Enclosure
from nefelibata.post import Post


@pytest.mark.asyncio
async def test_builder_setup(root: Path, config: Config) -> None:
    """
    Test that templates and build directory are created.
    """
    template_directory = root / "templates/builders/gemini"
    build_directory = root / "build/gemini"
    assert not template_directory.exists()
    assert not build_directory.exists()

    GeminiBuilder(root, config, "gemini://localhost:1965")
    last_update: Dict[Any, Any] = {}
    assert template_directory.exists()
    for file in ("index.gmi", "feed.gmi", "post.gmi"):
        assert (template_directory / file).exists()
        last_update[file] = (template_directory / file).stat().st_mtime
    assert build_directory.exists()
    last_update[build_directory] = build_directory.stat().st_mtime

    # on the second call the files and directories should be unmodified
    GeminiBuilder(root, config, "gemini://localhost:1965")
    for file in ("index.gmi", "feed.gmi", "post.gmi"):
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

    enclosure_path = post.path.parent / "picture.jpg"
    enclosure_path.touch()
    post.enclosures.append(
        Enclosure(
            path=enclosure_path,
            description="A photo",
            type="image/jpeg",
            length=666,
            href="first/picture.jpg",
        ),
    )

    builder = GeminiBuilder(root, config, "gemini://localhost:1965")
    with freeze_time("2021-01-02T00:00:00Z"):
        await builder.process_post(post)

    post_path = root / "build/gemini/first/index.gmi"

    # test that file was created
    assert post_path.exists()
    _logger.info.assert_has_calls(
        [
            mocker.call("Creating %s post", "Gemini"),
            mocker.call("Copying enclosure %s", enclosure_path),
        ],
    )
    with open(post_path, encoding="utf-8") as input_:
        content = input_.read()
    assert (
        content
        == """# This is your first post

# Welcome

This is your first post. It should be written using Markdown.

Read more about Nefelibata.

=> https://nefelibata.readthedocs.io/ Nefelibata

# Enclosures

=> gemini://localhost:1965/first/picture.jpg A photo

# Tags

=> gemini://localhost:1965/tags/blog.gmi blog
=> gemini://localhost:1965/tags/welcome.gmi welcome

# Categories

=> gemini://localhost:1965/categories/stem.gmi STEM

# About

Published on 2020-12-31 16:00:00-08:00 by Beto Dealmeida <roberto@dealmeida.net>.

=> gemini://localhost:1965 Go back to the main index"""
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
    _logger.info.assert_has_calls(
        [
            mocker.call("Creating %s post", "Gemini"),
            mocker.call("Copying enclosure %s", enclosure_path),
        ],
    )


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
    builder = GeminiBuilder(root, config, "gemini://localhost:1965")
    with freeze_time("2021-01-02T00:00:00Z"):
        await builder.process_site()

    assets_directory = root / "build/gemini"
    assets = (
        "index.gmi",
        "feed.gmi",
        "tags/welcome.gmi",
        "tags/blog.gmi",
        "categories/stem.gmi",
    )

    # test that files were created
    last_update: Dict[Any, Any] = {}
    for asset in assets:
        assert (assets_directory / asset).exists()
        last_update[asset] = (assets_directory / asset).stat().st_mtime
    _logger.info.assert_has_calls(
        [
            mocker.call("Creating %s", Path("/path/to/blog/build/gemini/index.gmi")),
            mocker.call("Creating %s", Path("/path/to/blog/build/gemini/feed.gmi")),
            mocker.call(
                "Creating %s",
                Path("/path/to/blog/build/gemini/tags/blog.gmi"),
            ),
            mocker.call(
                "Creating %s",
                Path("/path/to/blog/build/gemini/tags/welcome.gmi"),
            ),
            mocker.call(
                "Creating %s",
                Path("/path/to/blog/build/gemini/categories/stem.gmi"),
            ),
        ],
    )
    with open(assets_directory / "index.gmi", encoding="utf-8") as input_:
        content = input_.read()
    space = " "
    assert (
        content
        == f"""# 道&c.: Musings about the path and other things

This is the Gemini capsule of Beto Dealmeida.

=> https://taoetc.org/ Website
=> mailto://roberto@dealmeida.net Email address
=> gemini://localhost:1965/feed.gmi Gemlog

## Posts

=> gemini://localhost:1965/first/index.gmi 2020-12-31 16:00:00-08:00 — This is your first post{space}

## Links

=> https://2c.taoetc.org/@beto Mastodon

Crafted with ❤️ using Nefelibata

=> https://nefelibata.readthedocs.io/ Nefelibata"""
    )
    with open(assets_directory / "feed.gmi", encoding="utf-8") as input_:
        content = input_.read()
    assert (
        content
        == """# 道&c.

=> gemini://localhost:1965/first/index.gmi 2020-12-31 — This is your first post
"""
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
                Path("/path/to/blog/build/gemini/index.gmi"),
            ),
            mocker.call(
                "File %s is up-to-date, nothing to do",
                Path("/path/to/blog/build/gemini/feed.gmi"),
            ),
            mocker.call(
                "File %s is up-to-date, nothing to do",
                Path("/path/to/blog/build/gemini/tags/blog.gmi"),
            ),
            mocker.call(
                "File %s is up-to-date, nothing to do",
                Path("/path/to/blog/build/gemini/tags/welcome.gmi"),
            ),
            mocker.call(
                "File %s is up-to-date, nothing to do",
                Path("/path/to/blog/build/gemini/categories/stem.gmi"),
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
            mocker.call("Creating %s", Path("/path/to/blog/build/gemini/index.gmi")),
            mocker.call("Creating %s", Path("/path/to/blog/build/gemini/feed.gmi")),
            mocker.call(
                "Creating %s",
                Path("/path/to/blog/build/gemini/tags/blog.gmi"),
            ),
            mocker.call(
                "Creating %s",
                Path("/path/to/blog/build/gemini/tags/welcome.gmi"),
            ),
            mocker.call(
                "Creating %s",
                Path("/path/to/blog/build/gemini/categories/stem.gmi"),
            ),
        ],
    )


def test_gemini_renderer() -> None:
    """
    Test ``GeminiRenderer``.
    """
    double_space = "  "

    gemini = Markdown(renderer=GeminiRenderer)

    assert (
        gemini.convert(
            f"""
# Header 1

## Header 2

### Header 3

#### Header 4

- Mercury
- Gemini
  - Apollo

> This is{double_space}
> A multiline{double_space}
> blockquote{double_space}

*This* is a **paragraph**. With `code`.

This is an [inline link](https://example.com/). This is [another](https://example.org/).

```
This is some code.
```

End.
""",
        )
        == f"""
# Header 1

## Header 2

### Header 3

### Header 4

* Mercury
* Gemini
* Apollo

> This is
> A multiline
> blockquote{double_space}

This is a paragraph. With code.

This is an inline link. This is another.

=> https://example.com/ inline link
=> https://example.org/ another

```
This is some code.
```

End.
"""
    )


def test_gemini_renderer_link_ref_def() -> None:
    """
    Test rendering a link definition reference.
    """
    gemini = Markdown(renderer=GeminiRenderer)

    assert (
        gemini.convert(
            """
Hi, here's my [thing that I just casually mention][tt] sometimes.

[tt]: gemini://my.boring/url "I like this link"
            """,
        )
        == """
Hi, here's my thing that I just casually mention sometimes.

=> gemini://my.boring/url I like this link


"""
    )


def test_gemini_renderer_links() -> None:
    """
    Test rendering links.
    """
    gemini = Markdown(renderer=GeminiRenderer)
    assert (
        gemini.convert(
            """
This is a paragraph with [a link](https://example.com/). It is a good paragraph.

This one [also has a link](https://example.net/). It also has some *emphasis* and **bold**.

And this one is a special paragraph because it has not just [one](https://example.com/one),
but [two](https://example.com/two) links. That is quite a lot.

This other paragraph also has [a link][ref], using a reference. It's very fancy.

[ref]: https://example.org/foo "This is foo"

This one has an auto link <https://example.com/autolink>.

That is it.
            """,
        )
        == """
This is a paragraph with a link. It is a good paragraph.

=> https://example.com/ a link

This one also has a link. It also has some emphasis and bold.

=> https://example.net/ also has a link

And this one is a special paragraph because it has not just one,
but two links. That is quite a lot.

=> https://example.com/one one
=> https://example.com/two two

This other paragraph also has a link, using a reference. It's very fancy.

=> https://example.org/foo This is foo


This one has an auto link https://example.com/autolink.

=> https://example.com/autolink https://example.com/autolink

That is it.

"""
    )


def test_gemini_renderer_padding_after_link_ref_def() -> None:
    """
    Test the padding after a link reference definition.

    Ideally we shouldn't be left with an empty line.
    """
    gemini = Markdown(renderer=GeminiRenderer)
    assert (
        gemini.convert(
            """
This other paragraph also has [a link][ref], using a reference. It's very fancy.

[ref]: https://example.org/foo "This is foo"

That is it.
""",
        )
        == """
This other paragraph also has a link, using a reference. It's very fancy.

=> https://example.org/foo This is foo


That is it.
"""
    )


def test_gemini_renderer_image() -> None:
    """
    Test rendering images.
    """
    gemini = Markdown(renderer=GeminiRenderer)
    assert (
        gemini.convert(
            """
This is a paragraph.

![Alt text](https://assets.digitalocean.com/articles/alligator/boo.svg "a title")

![Alt text](https://assets.digitalocean.com/articles/alligator/boo.svg)

That is it.
""",
        )
        == """
This is a paragraph.

=> https://assets.digitalocean.com/articles/alligator/boo.svg a title

=> https://assets.digitalocean.com/articles/alligator/boo.svg Alt text

That is it.
"""
    )
