"""
Fake objects to simplify testing.
"""

from pathlib import Path

POST_DATA = {
    "path": Path("/path/to/blog/posts/first/index.mkd"),
    "title": "This is your first post",
    "timestamp": "2021-01-01T00:00:00Z",
    "metadata": {
        "keywords": "welcome, blog",
        "summary": "Hello, world!",
    },
    "tags": {"welcome", "blog"},
    "categories": ["stem"],
    "type": "post",
    "url": "first/index",
    "content": """# Welcome #

This is your first post. It should be written using Markdown.

Read more about [Nefelibata](https://nefelibata.readthedocs.io/).""",
}

POST_CONTENT = """subject: This is your first post
keywords: welcome, blog
summary: Hello, world!
# Welcome #

This is your first post. It should be written using Markdown.

Read more about [Nefelibata](https://nefelibata.readthedocs.io/)."""


CONFIG = {
    "title": "道&c.",
    "subtitle": "Musings about the path and other things",
    "author": {
        "name": "Beto Dealmeida",
        "url": "https://taoetc.org/",
        "email": "roberto@dealmeida.net",
        "note": "Este, sou eu",
    },
    "language": "en",
    "categories": {
        "stem": {
            "label": "STEM",
            "description": "Science, technology, engineering, & math",
            "tags": ["blog", "programming"],
        },
    },
}
