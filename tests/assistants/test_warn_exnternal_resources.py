from unittest import mock

from freezegun import freeze_time
from nefelibata.assistants.warn_external_resources import WarnExternalResourcesAssistant

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


def test_warn_external_resources(mock_post, requests_mock):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!

        This is an external image:

        ![alt text](https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png "Logo Title Text 1")

        This is a local one: ![alt text](img/test.png "Test")
        """,
        )
    post.create()

    config = {
        "url": "https://example.com/",
        "webmention": {"endpoint": "https://example.com/webmention"},
    }
    assistant = WarnExternalResourcesAssistant(config)

    with mock.patch(
        "nefelibata.assistants.warn_external_resources._logger",
    ) as mock_logger:
        assistant.process_post(post)

    mock_logger.warning.assert_called_with(
        "External resource found: https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png",
    )
