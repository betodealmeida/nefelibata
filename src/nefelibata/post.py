"""
A Nefelibata post (and associated functions).
"""

import asyncio
import operator
from datetime import datetime
from email.header import decode_header, make_header
from email.parser import Parser
from email.utils import formatdate, parsedate_to_datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set

import marko
from pydantic import BaseModel, PrivateAttr
from yarl import URL

from nefelibata.config import Config
from nefelibata.enclosure import Enclosure, get_enclosures
from nefelibata.utils import load_extra_metadata, split_header


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

    # special metadata
    tags: Set[str]
    categories: Set[str]
    announcers: Set[str]

    enclosures: List[Enclosure]

    # a custom type will use a custom template
    type: str

    # relative URL to the post, without any extensions, eg ``first/index``
    url: str

    # the Markdown contents of the file
    content: str

    # add a lock to manipulate the post file
    _lock: asyncio.Lock = PrivateAttr(default_factory=asyncio.Lock)


def build_post(root: Path, config: Config, path: Path) -> Post:
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

    metadata = {
        k: str(make_header(decode_header(v)))
        for k, v in parsed.items()
        if k not in required
    }
    type_ = metadata.get("type", "post")
    tags = split_header(metadata.get("keywords"))
    categories = {
        category_name
        for category_name, category_config in config.categories.items()
        if tags & set(category_config.tags)
    }

    if "announce-on" in metadata:
        announcers = split_header(metadata.get("announce-on"))
    else:
        announcers = set(config.announcers)
        parsed["announce-on"] = ", ".join(announcers)
        modified = True

    if modified:
        with open(path, "w", encoding="utf-8") as output:
            output.write(str(parsed))

    # load metadata from YAML files
    metadata.update(load_extra_metadata(path.parent))

    return Post(
        path=path,
        title=str(make_header(decode_header(parsed["subject"]))),
        timestamp=parsedate_to_datetime(parsed["date"]),
        metadata=metadata,
        tags=tags,
        categories=categories,
        announcers=announcers,
        enclosures=get_enclosures(root, path.parent),
        type=type_,
        url=str(path.relative_to(root / "posts").with_suffix("")),
        content=parsed.get_payload(decode=False),
    )


def get_posts(root: Path, config: Config, count: Optional[int] = None) -> List[Post]:
    """
    Return all the posts.

    Posts are sorted by timestamp in descending order.
    """
    paths = list((root / "posts").glob("**/*.mkd"))
    posts = sorted(
        (build_post(root, config, path) for path in paths),
        key=operator.attrgetter("timestamp"),
        reverse=True,
    )
    return posts[:count]  # a[:None] == a


def extract_links(post: Post) -> Iterator[URL]:
    """
    Extract all links from a post.

    This includes links in the content, as well as metadata.
    """
    for key, value in post.metadata.items():
        if key.endswith("-url"):
            yield URL(value)

    tree = marko.parse(post.content)
    queue = [tree]
    while queue:
        element = queue.pop(0)

        if isinstance(element, marko.inline.Link):
            yield URL(element.dest)
        elif hasattr(element, "children"):
            queue.extend(element.children)
