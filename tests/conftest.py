# -*- coding: utf-8 -*-
"""
    Dummy conftest.py for nefelibata.

    If you don't know what this is for, just leave it empty.
    Read more about conftest.py under:
    https://pytest.org/latest/plugins.html
"""
import textwrap
import time
from pathlib import Path
from typing import Any
from typing import Dict
from unittest.mock import MagicMock

import pytest
from nefelibata.post import Post


@pytest.fixture
def mock_post(fs):
    def build_post(markdown: str) -> Post:

        root = Path("/path/to/blog")
        fs.create_dir(root)

        fs.create_dir(root / "templates/test")
        with open(root / "templates/test/post.html", "w") as fp:
            fp.write(
                '<!DOCTYPE html><html lang="en"><head></head><body>{{ post.html }}</body></html>',
            )

        file_path = Path("/path/to/blog/posts/first/index.mkd")
        fs.create_file(file_path)

        contents = textwrap.dedent(markdown).strip()
        with open(file_path, "w") as fp:
            fp.write(contents)

        config: Dict[str, Any] = {"url": "https://example.com/", "theme": "test"}

        return Post(file_path, root, config)

    yield build_post
