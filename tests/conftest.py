"""
Fixtures for nefelibata.
"""
# pylint: disable=invalid-name, redefined-outer-name, unused-argument
from pathlib import Path
from typing import Any, Callable, Iterator, Type

import pytest
import yaml
from freezegun import freeze_time
from pyfakefs.fake_filesystem import FakeFilesystem

from nefelibata.config import Config
from nefelibata.constants import CONFIG_FILENAME
from nefelibata.post import Post, build_post
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
    # Add the templates to the fake filesystem, so builders can load them
    # during tests. The actual path depends if we're running in development
    # mode (``src/``) or installed (``site-packages``).
    root = get_project_root()
    locations = ("src/nefelibata/templates", "site-packages/nefelibata/templates")
    for location in locations:
        try:
            fs.add_real_directory(root / location)
        except FileNotFoundError:
            pass

    root = Path("/path/to/blog")
    fs.create_dir(root)
    yield root


@pytest.fixture
def config(fs: FakeFilesystem, root: Path) -> Iterator[Config]:
    """
    Create configuration file.
    """
    fs.create_file(root / CONFIG_FILENAME, contents=yaml.dump(CONFIG))

    yield Config(**CONFIG)


@pytest.fixture
def post(fs: FakeFilesystem, root: Path, config: Config) -> Iterator[Post]:
    """
    Create a post.
    """
    post_directory = root / "posts/first"
    post_path = post_directory / "index.mkd"
    with freeze_time("2021-01-01T00:00:00Z"):
        fs.create_file(post_path, contents=POST_CONTENT)
        post = build_post(root, config, post_path)

    yield post
