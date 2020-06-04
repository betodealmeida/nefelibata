import json
import logging
from datetime import datetime
from datetime import timezone
from typing import Union

import dateutil.parser
from dateutil.parser._parser import ParserError
from jinja2 import Environment
from jinja2 import FileSystemLoader
from nefelibata import __version__
from nefelibata.builders import Builder
from nefelibata.builders import Scope
from nefelibata.builders.utils import hash_n
from nefelibata.builders.utils import random_color
from nefelibata.post import Post

_logger = logging.getLogger(__name__)


class PostBuilder(Builder):

    scopes = [Scope.POST]

    def process_post(self, post: Post, force: bool = False) -> None:
        """Generate Atom feed.
        """
        if post.up_to_date and not force:
            return

        _logger.info("Creating post")

        post_directory = post.file_path.parent
        stylesheets = [
            path.relative_to(post_directory)
            for path in (post_directory / "css").glob("**/*.css")
        ]
        scripts = sorted(
            [
                path.relative_to(post_directory)
                for path in (post_directory / "js").glob("**/*.js")
            ],
        )
        json_ = {}
        for path in post_directory.glob("**/*.json"):
            with open(path) as fp:
                json_[path.stem] = json.load(fp)

        env = Environment(
            loader=FileSystemLoader(
                str(self.root / "templates" / self.config["theme"]),
            ),
        )
        env.filters["formatdate"] = jinja2_formatdate
        template = env.get_template("post.html")
        html = template.render(
            __version__=__version__,
            config=self.config,
            language=post.parsed.get("language") or self.config["language"],
            post=post,
            scripts=scripts,
            stylesheets=stylesheets,
            json=json_,
            breadcrumbs=[("Home", "/index.html"), (post.title, None)],
            hash_n=hash_n,
            random_color=random_color,
        )

        with open(post.file_path.with_suffix(".html"), "w") as fp:
            fp.write(html)


def jinja2_formatdate(obj: Union[str, int, float, datetime], fmt: str) -> str:
    """Jinja filter for formatting dates."""
    if isinstance(obj, str):
        try:
            obj = dateutil.parser.parse(obj).astimezone(timezone.utc)
        except ParserError:
            return "Unknown timestamp"
    elif isinstance(obj, (int, float)):
        obj = datetime.fromtimestamp(obj).astimezone(timezone.utc)
    return obj.strftime(fmt)
