import logging
import math
from collections import defaultdict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from nefelibata.post import get_posts, hash_n
from nefelibata.utils import find_external_resources, get_config, mirror_images

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
            breadcrumbs=[("Recent Posts", None)],
            previous=previous,
            next=next,
            hash_n=hash_n,
        )

        # mirror images locally
        html = mirror_images(html, root / "build" / "img")

        with open(root / "build" / name, "w") as fp:
            fp.write(html)
        previous, name = name, next

        for resource in find_external_resources(html):
            _logger.warning(f"External resource found: {resource}")


def create_categories(root: Path) -> None:
    """Generate pages for each category.

    Args:
      root (str): directory where the weblog lives
    """
    config = get_config(root)
    env = Environment(
        loader=FileSystemLoader(str(root / "templates" / config["theme"]))
    )
    template = env.get_template("index.html")

    posts = get_posts(root)
    categories = defaultdict(list)
    for post in posts:
        for category in post.parsed.get("keywords", "").split(","):
            categories[category.strip()].append(post)

    for category, posts in categories.items():
        posts.sort(key=lambda x: x.date, reverse=True)
        last_modified = max(post.file_path.stat().st_mtime for post in posts)
        show = config.get("posts-to-show", 10)
        pages = int(math.ceil(len(posts) / show))
        previous, name = None, f"{category}.html"
        for page in range(pages):
            filename = root / "build" / name

            # only update if there are changes to files in this category
            if filename.exists() and filename.stat().st_mtime > last_modified:
                continue

            if page + 1 < pages:
                next = f"{category}%d.html" % (page + 1)
            else:
                next = None
            html = template.render(
                config=config,
                posts=posts[page * show : (page + 1) * show],
                breadcrumbs=[
                    ("Home", "/index.html"),
                    (f'Posts about "{category}"', None),
                ],
                previous=previous,
                next=next,
                hash_n=hash_n,
            )

            # mirror images locally
            html = mirror_images(html, root / "build" / "img")

            with open(filename, "w") as fp:
                fp.write(html)
            previous, name = name, next

            for resource in find_external_resources(html):
                _logger.warning(f"External resource found: {resource}")


def create_feed(root: Path) -> None:
    """Generate Atom feed.

    Args:
      root (str): directory where the weblog lives
    """
    config = get_config(root)
    env = Environment(loader=FileSystemLoader(str(root / "templates")))
    template = env.get_template("atom.xml")

    posts = get_posts(root)
    posts.sort(key=lambda x: x.date, reverse=True)
    show = config.get("posts-to-show", 10)
    xml = template.render(config=config, posts=posts[:show])
    with open(root / "build" / "atom.xml", "w") as fp:
        fp.write(xml)
