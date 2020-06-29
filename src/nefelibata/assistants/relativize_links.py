import logging
import urllib.parse
from pathlib import Path

from bs4 import BeautifulSoup
from nefelibata.assistants import Assistant
from nefelibata.assistants import Scope
from nefelibata.post import Post
from nefelibata.utils import modify_html

_logger = logging.getLogger(__name__)


class RelativizeLinksAssistant(Assistant):

    scopes = [Scope.POST, Scope.SITE]

    def process_post(self, post: Post, force: bool = False) -> None:
        self._process_file(post.file_path.with_suffix(".html"))

    def process_site(self, force: bool = False) -> None:
        for path in (self.root / "build").glob("*.html"):
            self._process_file(path)

    def _process_file(self, file_path: Path) -> None:
        tag_attributes = [
            ("a", "href"),
            ("img", "src"),
            ("link", "href"),
            ("script", "src"),
        ]
        soup: BeautifulSoup
        with modify_html(file_path) as soup:
            for tag, attr in tag_attributes:
                for el in soup.find_all(tag):
                    resource = el.attrs.get(attr)
                    if not resource:
                        continue

                    # this should be "posts", when `process_post` is called, or "build",
                    # when `process_site` is called
                    base_dir = file_path.relative_to(self.root).parts[0]

                    if resource.startswith(self.config["url"]):
                        resource_path = (
                            self.root / base_dir / resource[len(self.config["url"]) :]
                        )
                    elif resource.startswith("/"):
                        resource_path = self.root / base_dir / resource[1:]
                    else:
                        _logger.debug("Relative link found, ignoring")
                        continue

                    # for relative paths that are in higher directories we need to
                    # manually add .. until we reach it
                    up = Path(".")
                    parent = file_path.parent
                    while True:
                        try:
                            # we're guaranteed to reach this eventually
                            relative_url = resource_path.relative_to(parent)
                            break
                        except ValueError:
                            # resource is up of file path
                            parent = parent.parent
                            up = up / ".."

                    el.attrs[attr] = up / relative_url
