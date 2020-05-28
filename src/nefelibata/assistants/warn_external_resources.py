import logging
import urllib.parse
from pathlib import Path

from bs4 import BeautifulSoup
from nefelibata.assistants import Assistant
from nefelibata.assistants import Scope
from nefelibata.post import Post

_logger = logging.getLogger("nefelibata")


class WarnExternalResourcesAssistant(Assistant):

    scopes = [Scope.POST, Scope.SITE]

    def process_post(self, post: Post) -> None:
        _logger.warning("test")
        self.process_site(post.file_path.with_suffix(".html"))

    def process_site(self, file_path: Path) -> None:
        with open(file_path) as fp:
            html = fp.read()

        self._process_html(html)

    def _process_html(self, html: str) -> None:
        safelist = [
            urllib.parse.urljoin(self.config["url"], "atom.xml"),
            self.config["webmention"]["endpoint"],  # Use .get
        ]

        tag_attributes = [
            ("img", "src"),
            ("link", "href"),
            ("script", "src"),
        ]
        soup = BeautifulSoup(html, "html.parser")
        for tag, attr in tag_attributes:
            for el in soup.find_all(tag):
                resource = el.attrs.get(attr)
                if resource and "://" in resource and resource not in safelist:
                    _logger.warning(f"External resource found: {resource}")
