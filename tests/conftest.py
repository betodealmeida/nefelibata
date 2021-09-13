"""
    Dummy conftest.py for nefelibata.

    If you don't know what this is for, just leave it empty.
    Read more about conftest.py under:
    - https://docs.pytest.org/en/stable/fixture.html
    - https://docs.pytest.org/en/stable/writing_plugins.html
"""
# pylint: disable=invalid-name, redefined-outer-name, unused-argument
from pathlib import Path
from typing import Any, Callable, Iterator, Type

import pytest
import yaml
from freezegun import freeze_time
from pyfakefs.fake_filesystem import FakeFilesystem

from nefelibata.constants import CONFIG_FILENAME
from nefelibata.post import Post, build_post
from nefelibata.typing import Config
from nefelibata.utils import get_project_root

from .fakes import CONFIG, POST_CONTENT


class MockEntryPoint:  # pylint: disable=too-few-public-methods
    """
    A class for mocking entry points.
    """

    def __init__(self, name: str, class_: Callable[..., Any]):
        self.name = name
        self.class_ = class_

    def load(self) -> Callable[..., Any]:
        """
        Return the class.
        """
        return self.class_


@pytest.fixture
def make_entry_point() -> Type[MockEntryPoint]:
    """
    Fixture for a helper function to mock entry points.
    """
    return MockEntryPoint


@pytest.fixture
def root(fs: FakeFilesystem) -> Iterator[Path]:
    """
    Create the blog root directory.
    """
    root = get_project_root()
    fs.add_real_directory(root / "src/nefelibata/templates")

    root = Path("/path/to/blog")
    fs.create_dir(root)
    yield root


@pytest.fixture
def config(fs: FakeFilesystem, root: Path) -> Iterator[Config]:
    """
    Create configuration file.
    """
    with open(root / CONFIG_FILENAME, "w", encoding="utf-8") as output:
        output.write(yaml.dump(CONFIG))

    yield CONFIG.copy()


@pytest.fixture
def post(fs: FakeFilesystem, root: Path) -> Iterator[Post]:
    """
    Create a post.
    """
    post_directory = root / "posts/first"
    post_path = post_directory / "index.mkd"
    fs.create_dir(post_directory)
    with freeze_time("2021-01-01T00:00:00Z"):
        with open(post_path, "w", encoding="utf-8") as output:
            output.write(POST_CONTENT)
        post = build_post(root, post_path)

    yield post
