import logging
from collections import defaultdict
from pathlib import Path
from typing import Optional

from jinja2 import Environment
from jinja2 import FileSystemLoader
from nefelibata import __version__
from nefelibata.builders import Builder
from nefelibata.builders import Scope
from nefelibata.builders.utils import hash_n
from nefelibata.builders.utils import random_color
from nefelibata.post import get_posts

_logger = logging.getLogger(__name__)


class TagsBuilder(Builder):

    scopes = [Scope.SITE]

    def process_site(self, force: bool = False) -> None:
        """Generate pages for each tag.
        """
        _logger.info("Creating tags pages")

        env = Environment(
            loader=FileSystemLoader(
                str(self.root / "templates" / self.config["theme"]),
            ),
        )
        template = env.get_template("index.html")

        posts = get_posts(self.root)
        tags = defaultdict(list)
        for post in posts:
            for tag in post.parsed.get("keywords", "").split(","):
                tags[tag.strip()].append(post)

        for tag, posts in tags.items():
            posts.sort(key=lambda x: x.date, reverse=True)
            last_modified = max(post.file_path.stat().st_mtime for post in posts)
            show = self.config.get("posts-to-show", 10)

            # first page; these will be updated
            page = 1
            name: Optional[str] = f"{tag}.html"
            previous: Optional[str] = None

            while name:
                page_posts, posts = posts[:show], posts[show:]

                file_path = self.root / "build" / name

                # only update if there are changes to files in this tag
                if (
                    not force
                    and file_path.exists()
                    and file_path.stat().st_mtime > last_modified
                ):
                    break

                # link to next page
                next = f"{tag}{page}.html" if posts else None

                html = template.render(
                    __version__=__version__,
                    config=self.config,
                    language=self.config["language"],
                    posts=page_posts,
                    breadcrumbs=[
                        ("Home", "/index.html"),
                        (f'Posts tagged "{tag}"', None),
                    ],
                    previous=previous,
                    next=next,
                    hash_n=hash_n,
                    random_color=random_color,
                )

                with open(file_path, "w") as fp:
                    fp.write(html)

                page += 1
                previous, name = name, next
