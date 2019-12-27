import math
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from nefelibata.post import hash_n
from nefelibata.utils import get_config, get_posts


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
