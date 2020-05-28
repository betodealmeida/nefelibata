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


class TestAssistant(Assistant):

    scope = [Scope.POST]


def make_dummy_assistant(scope):
    return type("SomeAssistant", (Assistant,), {"scope": scope})


class TestEntryPoint:
    def __init__(self, name: str, assistant: Assistant):
        self.name = name
        self.assistant = assistant

    def load(self) -> Assistant:
        return self.assistant


def test_get_assistants(mock_post, mocker):
    entry_points = [
        TestEntryPoint("test1", make_dummy_assistant(Scope.POST)),
        TestEntryPoint("test2", make_dummy_assistant(Scope.SITE)),
    ]
    mocker.patch("nefelibata.assistants.iter_entry_points", return_value=entry_points)

    config = {
        "url": "https://blog.example.com/",
        "language": "en",
        "assistants": ["test2"],
        "test1": {},
        "test2": {},
    }

    assistants = get_assistants(config, Scope.POST)
    assert len(assistants) == 1
    assert assistants[0].scope == Scope.SITE


def test_wrong_scope(mock_post):
    post_assistant = make_dummy_assistant([Scope.POST])()
    with pytest.raises(Exception) as excinfo:
        post_assistant.process_site(Path("/path/to/blog"))

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

    site_assistant = make_dummy_assistant([Scope.SITE])()
    with pytest.raises(Exception) as excinfo:
        site_assistant.process_post(post)

    assert str(excinfo.value) == 'Scope "post" not supported by SomeAssistant'
