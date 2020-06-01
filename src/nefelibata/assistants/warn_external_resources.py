import logging
import urllib.parse
from pathlib import Path

import tinycss2
from bs4 import BeautifulSoup
from nefelibata.assistants import Assistant
from nefelibata.assistants import Scope
from nefelibata.post import Post

_logger = logging.getLogger("nefelibata")


class WarnExternalResourcesAssistant(Assistant):

    scopes = [Scope.POST, Scope.SITE]

    def process_post(self, post: Post) -> None:
        self._process_file(post.file_path.with_suffix(".html"))

    def process_site(self) -> None:
        for path in (self.root / "build").glob("*.html"):
            self._process_file(path)

    def _safe(self, resource: str):
        # any URL that starts with the blog URL is safe
        if resource.startswith(self.config["url"]):
            return True

        # if the blog uses an external endpoint for webmention that's ok
        if (
            "webmention" in self.config
            and resource == self.config["webmention"]["endpoint"]
        ):
            return True

        return False

    def _process_file(self, file_path: Path) -> None:
        with open(file_path) as fp:
            html = fp.read()

        tag_attributes = [
            ("img", "src"),
            ("link", "href"),
            ("script", "src"),
        ]
        soup = BeautifulSoup(html, "html.parser")
        for tag, attr in tag_attributes:
            for el in soup.find_all(tag):
                resource = el.attrs.get(attr)
                if not resource:
                    continue
                if "://" in resource and not self._safe(resource):
                    _logger.warning(f"External resource found: {resource}")
                if resource.endswith(".css"):
                    self._check_css(resource, file_path)

    def _check_css(self, resource: str, file_path: Path) -> None:
        """Check CSS for external URLs."""
        if "://" in resource and not resource.startswith(self.config["url"]):
            # external CSS, should've been already flagged
            return

        if resource.startswith("/"):
            css_path = self.root / "build" / resource[1:]
        else:
            css_path = file_path.parent / resource

        with open(css_path) as fp:
            css = fp.read()

        stylesheet = tinycss2.parse_stylesheet(
            css, skip_comments=True, skip_whitespace=True,
        )
        for rule in stylesheet:
            for token in rule.content:
                if (
                    isinstance(token, tinycss2.ast.URLToken)
                    and "://" in token.value
                    and not self._safe(token.value)
                ):
                    _logger.warning(
                        f"External resource found in {css_path}: {token.value}",
                    )
