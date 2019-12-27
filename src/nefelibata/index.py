import logging
import math
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from nefelibata.post import get_posts, hash_n
from nefelibata.utils import find_external_resources, get_config

_logger = logging.getLogger("nefelibata")


def create_index(root: Path) -> None:
    """Generate index and archives.

    Args:
      root (str): directory where the weblog lives
    """
    config = get_config(root)
    env = Environment(
        loader=FileSystemLoader(str(root / "templates" / config["theme"]))
    )
    template = env.get_template("index.html")

    posts = get_posts(root)
    posts.sort(key=lambda x: x.date, reverse=True)
    show = config.get("posts-to-show", 10)
    pages = int(math.ceil(len(posts) / show))
    previous, name = None, "index.html"
    for page in range(pages):
        if page + 1 < pages:
            next = "archive%d.html" % (page + 1)
        else:
            next = None
        html = template.render(
            config=config,
            posts=posts[page * show : (page + 1) * show],
            breadcrumbs=[("Home", None)],
            previous=previous,
            next=next,
            hash_n=hash_n,
        )
        with open(root / "build" / name, "w") as fp:
            fp.write(html)
        previous, name = name, next

        for resource in find_external_resources(html):
            _logger.warning(f"External resource found: {resource}")
