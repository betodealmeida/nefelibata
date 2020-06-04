import logging
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


class IndexBuilder(Builder):

    scopes = [Scope.SITE]

    def process_site(self, force: bool = True) -> None:
        """Generate index and archives.
        """
        _logger.info("Creating index")

        env = Environment(
            loader=FileSystemLoader(
                str(self.root / "templates" / self.config["theme"]),
            ),
        )
        template = env.get_template("index.html")

        posts = get_posts(self.root)
        posts.sort(key=lambda x: x.date, reverse=True)
        show = self.config.get("posts-to-show", 10)

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
                config=self.config,
                language=self.config["language"],
                posts=page_posts,
                breadcrumbs=[("Recent Posts", None)],
                previous=previous,
                next=next,
                hash_n=hash_n,
                random_color=random_color,
            )

            file_path = self.root / "build" / name
            with open(file_path, "w") as fp:
                fp.write(html)

            page += 1
            previous, name = name, next
