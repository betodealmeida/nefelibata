import hashlib
import time
from datetime import datetime
from email.parser import Parser
from email.utils import formatdate, parsedate
from pathlib import Path
from typing import Any, Dict

import markdown
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader


class Post:
    def __init__(self, file_path: Path, root: Path, config: Dict[str, Any]):
        self.file_path = file_path
        self.root = root
        self.config = config

        with open(file_path) as fp:
            self.parsed = Parser().parse(fp)

        self.markdown = self.parsed.get_payload(decode=True).decode("utf-8")
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
        return self.file_path.relative_to(self.root / "posts").with_suffix(".html")

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
        """
        post_directory = self.file_path.parent
        stylesheets = [
            path.relative_to(post_directory)
            for path in (post_directory / "css").glob("**/*.css")
        ]
        scripts = sorted([
            path.relative_to(post_directory)
            for path in (post_directory / "js").glob("**/*.js")
        ])

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
            breadcrumbs=[('Home', '..'), (self.title, None)],
            hash_n=hash_n,
        )
        filename = self.file_path.with_suffix(".html")
        with open(filename, "w") as fp:
            fp.write(html)


def jinja2_formatdate(obj, fmt):
    """Jinja filter for formatting dates."""
    if isinstance(obj, basestring):
        obj = dateutil.parser.parse(obj)
    return obj.strftime(fmt)


def hash_n(text: str, numbers: int = 10) -> int:
    """Hash a string into a number between 0 and `numbers-1`.

    Args:
      text (str): a string to be hashed
      numbers (int): hash string to a number between 0 and `numbers-1`
    """
    return int(hashlib.md5(text).hexdigest(), 16) % numbers
