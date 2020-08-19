import logging
import time
from datetime import datetime
from email.header import decode_header
from email.header import make_header
from email.parser import Parser
from email.utils import formatdate
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from typing import cast
from typing import Dict
from typing import List

import markdown
from bs4 import BeautifulSoup

_logger = logging.getLogger(__name__)


class Post:
    def __init__(self, file_path: Path):
        self.file_path = file_path

        with open(file_path) as fp:
            self.parsed = Parser().parse(fp)

        self.markdown = self.parsed.get_payload(decode=False)
        self.html = markdown.markdown(
            self.markdown, extensions=["codehilite"], output_format="html5",
        )
        self.update_metadata()

    @property
    def title(self) -> str:
        return str(make_header(decode_header(self.parsed["subject"])))

    @property
    def summary(self) -> str:
        if self.parsed["summary"]:
            return str(make_header(decode_header(self.parsed["summary"])))

        soup = BeautifulSoup(self.html, "html.parser")
        if soup.p:
            summary: str = soup.p.text.replace("\n", " ")
            if len(summary) > 140:
                summary = summary[:139] + "\u2026"
            return summary

        return "No summary."

    @property
    def date(self) -> datetime:
        if not self.parsed["date"]:
            raise Exception(f"Missing date on file {self.file_path}")
        return parsedate_to_datetime(self.parsed["date"])

    @property
    def url(self) -> str:
        post_directory = self.file_path.parent
        # TODO: this should be relative to root/posts instead
        return str(
            self.file_path.relative_to(post_directory.parent).with_suffix(".html"),
        )

    @property
    def up_to_date(self) -> bool:
        html = self.file_path.with_suffix(".html")
        return html.exists() and html.stat().st_mtime >= self.file_path.stat().st_mtime

    def update_metadata(self) -> None:
        """Automatically generate date and subject headers.
        """
        modified = False

        if not self.parsed.get("date"):
            date = self.file_path.stat().st_mtime
            self.parsed["date"] = formatdate(date, localtime=True)
            modified = True

        if not self.parsed.get("subject"):
            # try to find an H1 tag or use the filename
            soup = BeautifulSoup(self.html, "html.parser")
            del self.parsed["subject"]  # needed to overwrite
            if soup.h1:
                self.parsed["subject"] = soup.h1.text
            else:
                # use directory name
                self.parsed["subject"] = str(self.file_path.parent.name)
            modified = True

        if modified:
            self.save()

    def save(self) -> None:
        """Save post back."""
        with open(self.file_path, "w") as fp:
            fp.write(str(self.parsed))


def get_posts(root: Path) -> List[Post]:
    """Return list of posts for a given root directory.
    """
    return [Post(source) for source in (root / "posts").glob("**/*.mkd")]
