"""
A Nefelibata post (and associated functions).
"""
from datetime import datetime
from email.header import decode_header, make_header
from email.parser import Parser
from email.utils import formatdate, parsedate_to_datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Post(BaseModel):  # pylint: disable=too-few-public-methods
    """
    Model representing a post.
    """

    # path to the post
    path: Path

    # the title of the post, stored in the "subject" header
    title: str

    # post creation timestamp, stored in the "date" header
    timestamp: datetime

    # all the headers from the post
    metadata: Dict[str, Any]

    # relative URL to the post, without any extensions
    # eg: first/index
    url: str

    # the Markdown contents of the file
    content: str


def build_post(root: Path, path: Path) -> Post:
    """
    Build a post from a file path.

    Each post is stored in a file as an email.
    """
    with open(path, encoding="utf-8") as input_:
        parsed = Parser().parse(input_)

    # set default for missing values
    required = {
        "subject": "No subject found",
        "date": formatdate(path.stat().st_mtime, localtime=True),
    }
    modified = False
    for header, default in required.items():
        if header not in parsed:
            parsed[header] = default
            modified = True
    if modified:
        with open(path, "w", encoding="utf-8") as input_:
            input_.write(str(parsed))

    metadata = {k: v for k, v in parsed.items() if k not in required}

    return Post(
        path=path,
        title=str(make_header(decode_header(parsed["subject"]))),
        timestamp=parsedate_to_datetime(parsed["date"]),
        metadata=metadata,
        url=str(path.relative_to(root / "posts").with_suffix("")),
        content=parsed.get_payload(decode=False),
    )


def get_posts(root: Path, count: Optional[int] = None) -> List[Post]:
    """
    Return all the posts.
    """

    paths = list((root / "posts").glob("**/*.mkd"))
    paths.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    paths = paths[:count]  # a[:None] == a

    return [build_post(root, path) for path in paths]
