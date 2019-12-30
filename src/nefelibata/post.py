import hashlib
import json
import logging
import time
from datetime import datetime
from email.parser import Parser
from email.utils import formatdate, parsedate
from pathlib import Path
from typing import Any, Dict, List

import dateutil.parser
import markdown
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from nefelibata.utils import find_external_resources, get_config, mirror_images

_logger = logging.getLogger("nefelibata")


class Post:
    def __init__(self, file_path: Path, root: Path, config: Dict[str, Any]):
        self.file_path = file_path
        self.root = root
        self.config = config

        with open(file_path) as fp:
            self.parsed = Parser().parse(fp)

        self.markdown = self.parsed.get_payload(decode=False)
        self.html = markdown.markdown(
            self.markdown, extensions=["codehilite"], output_format="html5",
        )
        self.update_metadata()

    @property
    def title(self) -> str:
        return self.parsed["subject"]

    @property
    def summary(self) -> str:
        if self.parsed["summary"] is not None:
            return self.parsed["summary"]

        soup = BeautifulSoup(self.html, "html.parser")
        if soup.p:
            summary = soup.p.text
            if len(summary) > 140:
                summary = summary[:140] + "&#8230;"
            return summary

        return "No summary."

    @property
    def date(self) -> datetime:
        return datetime.fromtimestamp(time.mktime(parsedate(self.parsed["date"])))

    @property
    def url(self) -> str:
        return str(self.file_path.relative_to(self.root / "posts").with_suffix(".html"))

    @property
    def up_to_date(self) -> bool:
        html = self.file_path.with_suffix(".html")
        return html.exists() and html.stat().st_mtime >= self.file_path.stat().st_mtime

    def update_metadata(self) -> None:
        """Automatically generate date and subject headers.
        """
        modified = False

        if "date" not in self.parsed:
            date = self.file_path.stat().st_mtime
            self.parsed["date"] = formatdate(date, localtime=True)
            modified = True

        if "subject" not in self.parsed:
            # try to find an H1 tag or use the filename
            soup = BeautifulSoup(self.html, "html.parser")
            if soup.h1:
                self.parsed["subject"] = soup.h1.text
            else:
                self.parsed["subject"] = self.file_path.name
            modified = True

        if modified:
            self.save()

    def save(self) -> None:
        """Save post back."""
        with open(self.file_path, "w") as fp:
            fp.write(str(self.parsed))

    def create(self) -> None:
        """Convert post from Markdown to HTML.

        TODO: move to utils.py
        """
        post_directory = self.file_path.parent
        stylesheets = [
            path.relative_to(post_directory)
            for path in (post_directory / "css").glob("**/*.css")
        ]
        scripts = sorted(
            [
                path.relative_to(post_directory)
                for path in (post_directory / "js").glob("**/*.js")
            ]
        )
        json_ = {}
        for path in post_directory.glob("**/*.json"):
            with open(path) as fp:
                json_[path.stem] = json.load(fp)

        env = Environment(
            loader=FileSystemLoader(str(self.root / "templates" / self.config["theme"]))
        )
        env.filters["formatdate"] = jinja2_formatdate
        template = env.get_template("post.html")
        html = template.render(
            config=self.config,
            post=self,
            scripts=scripts,
            stylesheets=stylesheets,
            json=json_,
            breadcrumbs=[("Home", "/index.html"), (self.title, None)],
            hash_n=hash_n,
        )

        # mirror images locally
        html = mirror_images(html, post_directory / "img")

        filename = self.file_path.with_suffix(".html")
        with open(filename, "w") as fp:
            fp.write(html)

        for resource in find_external_resources(html):
            _logger.warning(f"External resource found: {resource}")


def jinja2_formatdate(obj, fmt: str) -> str:
    """Jinja filter for formatting dates."""
    if isinstance(obj, str):
        obj = dateutil.parser.parse(obj)
    elif isinstance(obj, (int, float)):
        obj = datetime.fromtimestamp(obj)
    return obj.strftime(fmt)


def hash_n(text: bytes, numbers: int = 10) -> int:
    """Hash a string into a number between 0 and `numbers-1`.

    Args:
      text (str): a string to be hashed
      numbers (int): hash string to a number between 0 and `numbers-1`
    """
    return int(hashlib.md5(text).hexdigest(), 16) % numbers


def get_posts(root: Path) -> List[Post]:
    """Return list of posts for a given root directory.

    Args:
      root (str): directory where the weblog lives
    """
    config = get_config(root)
    return [Post(source, root, config) for source in (root / "posts").glob("**/*.mkd")]
