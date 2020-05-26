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
def mock_post(fs, mocker):
    def build_post(markdown: str) -> Post:

        root = Path("/path/to/blog")
        fs.create_dir(root)

        file_path = Path("/path/to/blog/posts/first/index.mkd")
        fs.create_file(file_path)

        content = textwrap.dedent(markdown).strip()
        mock_open = mocker.mock_open(read_data=content)

        config: Dict[str, Any] = {}

        mocker.patch("nefelibata.post.open", mock_open)
        return Post(file_path, root, config)

    yield build_post
