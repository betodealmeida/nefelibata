from pathlib import Path
from typing import Any
from typing import Dict
from unittest import mock

from freezegun import freeze_time
from nefelibata.assistants.warn_external_resources import WarnExternalResourcesAssistant
from nefelibata.builders.post import PostBuilder

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


config: Dict[str, Any] = {
    "url": "https://example.com/",
    "language": "en",
    "theme": "test-theme",
    "webmention": {"endpoint": "https://webmention.io/example.com/webmention"},
}


def test_warn_external_resources(mock_post):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!

        This is an external image:

        ![alt text](https://external.example.com/icon48.png "Logo Title Text 1")

        This is a local one: ![alt text](img/test.png "Test")

        This is a safe one: ![alt text](https://example.com/icon48.png)

        This is an image tag without a source: <img />
        """,
        )
    PostBuilder(root, config).process_post(post)

    assistant = WarnExternalResourcesAssistant(root, config)

    with mock.patch(
        "nefelibata.assistants.warn_external_resources._logger",
    ) as mock_logger:
        assistant.process_post(post)

    mock_logger.warning.assert_has_calls(
        [
            mock.call(
                "External resource found: https://external.example.com/icon48.png",
            ),
            mock.call(
                "External resource found: https://external.example.com/css/basic.css",
            ),
        ],
    )


def test_warn_external_resources_css(mock_post, fs):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!
        """,
        )

    # add external css
    post_directory = post.file_path.parent
    fs.create_dir(post_directory / "css")
    with open(post_directory / "css" / "test.css", "w") as fp:
        fp.write(
            """
body {
  background: url("https://external.example.com/icon48.png");
}
        """,
        )

    PostBuilder(root, config).process_post(post)

    assistant = WarnExternalResourcesAssistant(root, config)

    with mock.patch(
        "nefelibata.assistants.warn_external_resources._logger",
    ) as mock_logger:
        assistant.process_post(post)

    mock_logger.warning.assert_called_with(
        "External resource found in /path/to/blog/posts/first/css/test.css: https://external.example.com/icon48.png",
    )


def test_process_site(mock_post, mocker, requests_mock, fs):
    root = Path("/path/to/blog")

    fs.create_dir(root / "build")
    with open(root / "build/about.html", "w") as fp:
        fp.write(
            '<img src="https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png" />',
        )

    assistant = WarnExternalResourcesAssistant(root, config)

    with mock.patch(
        "nefelibata.assistants.warn_external_resources._logger",
    ) as mock_logger:
        assistant.process_site()

    mock_logger.warning.assert_called_with(
        "External resource found: https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png",
    )
