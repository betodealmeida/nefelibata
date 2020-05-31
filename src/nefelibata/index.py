import logging
import math
from collections import defaultdict
from pathlib import Path
from typing import Optional

from jinja2 import Environment
from jinja2 import FileSystemLoader
from nefelibata import __version__
from nefelibata.assistants import get_assistants
from nefelibata.assistants import Scope
from nefelibata.post import get_posts
from nefelibata.post import hash_n
from nefelibata.utils import get_config


def create_index(root: Path) -> None:
    """Generate index and archives.

    Args:
      root (str): directory where the weblog lives
    """
    config = get_config(root)
    site_assistants = get_assistants(root, config, Scope.SITE)
    env = Environment(
        loader=FileSystemLoader(str(root / "templates" / config["theme"])),
    )
    template = env.get_template("index.html")

    posts = get_posts(root)
    posts.sort(key=lambda x: x.date, reverse=True)
    show = config.get("posts-to-show", 10)

    # first page; these will be updated
    page = 1
    name: Optional[str] = "index.html"
    previous: Optional[str] = None

    while name:
        page_posts, posts = posts[:show], posts[show:]

        # link to next page
        next = f"archive{page}.html" if posts else None

        html = template.render(
            __version__=__version__,
            config=config,
            posts=page_posts,
            breadcrumbs=[("Recent Posts", None)],
            previous=previous,
            next=next,
            hash_n=hash_n,
        )

        file_path = root / "build" / name
        with open(file_path, "w") as fp:
            fp.write(html)

        for assistant in site_assistants:
            assistant.process_site(file_path)

        page += 1
        previous, name = name, next


def create_categories(root: Path) -> None:
    """Generate pages for each category.

    Args:
      root (str): directory where the weblog lives
    """
    config = get_config(root)
    site_assistants = get_assistants(root, config, Scope.SITE)
    env = Environment(
        loader=FileSystemLoader(str(root / "templates" / config["theme"])),
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

        # first page; these will be updated
        page = 1
        name: Optional[str] = f"{category}.html"
        previous: Optional[str] = None

        while name:
            page_posts, posts = posts[:show], posts[show:]

            file_path = root / "build" / name

            # only update if there are changes to files in this category
            if file_path.exists() and file_path.stat().st_mtime > last_modified:
                break

            # link to next page
            next = f"{category}{page}.html" if posts else None

            html = template.render(
                __version__=__version__,
                config=config,
                posts=page_posts,
                breadcrumbs=[
                    ("Home", "/index.html"),
                    (f'Posts about "{category}"', None),
                ],
                previous=previous,
                next=next,
                hash_n=hash_n,
            )

            with open(file_path, "w") as fp:
                fp.write(html)

            for assistant in site_assistants:
                assistant.process_site(file_path)

            page += 1
            previous, name = name, next


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
