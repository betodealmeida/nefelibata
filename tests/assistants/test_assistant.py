from pathlib import Path

import pytest
from freezegun import freeze_time
from nefelibata.assistants import Assistant
from nefelibata.assistants import get_assistants
from nefelibata.assistants import Scope
from nefelibata.post import Post

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


class MockAssistant(Assistant):

    scopes = [Scope.POST]


def make_dummy_assistant(scope):
    return type("SomeAssistant", (Assistant,), {"scopes": [scope]})


class MockEntryPoint:
    def __init__(self, name: str, assistant: Assistant):
        self.name = name
        self.assistant = assistant

    def load(self) -> Assistant:
        return self.assistant


def test_get_assistants(mocker):
    root = Path("/path/to/blog")
    entry_points = [
        MockEntryPoint("test1", make_dummy_assistant(Scope.POST)),
        MockEntryPoint("test2", make_dummy_assistant(Scope.SITE)),
    ]
    mocker.patch("nefelibata.assistants.iter_entry_points", return_value=entry_points)

    config = {
        "url": "https://blog.example.com/",
        "language": "en",
        "assistants": ["test1", "test2"],
        "test1": {},
        "test2": {},
    }

    assistants = get_assistants(root, config, Scope.POST)
    assert len(assistants) == 1
    assert assistants[0].scopes == [Scope.POST]


def test_wrong_scope(mock_post):
    root = Path("/path/to/blog")
    config = {}

    post_assistant = make_dummy_assistant([Scope.POST])(root, config)
    with pytest.raises(Exception) as excinfo:
        post_assistant.process_site()

    assert str(excinfo.value) == 'Scope "site" not supported by SomeAssistant'

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: test
        keywords: test
        summary: A simple test

        Hello, there!
        """,
        )

    site_assistant = make_dummy_assistant([Scope.SITE])(root, config)
    with pytest.raises(Exception) as excinfo:
        site_assistant.process_post(post)

    assert str(excinfo.value) == 'Scope "post" not supported by SomeAssistant'
