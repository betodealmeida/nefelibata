import json
import logging
import re
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from nefelibata.assistants import Assistant
from nefelibata.assistants import Scope
from nefelibata.post import Post

_logger = logging.getLogger(__name__)


class ArchiveLinksAssistant(Assistant):

    scopes = [Scope.POST]

    def _safe(self, resource: str):
        if resource.startswith(self.config["url"]):
            return True

        # if the blog uses an external endpoint for webmention that's ok
        if (
            "webmention" in self.config
            and resource == self.config["webmention"]["endpoint"]
        ):
            return True

        # ignore links to archive itself
        parsed = urllib.parse.urlparse(resource)
        return parsed.netloc.endswith("archive.org")

    def process_post(self, post: Post, force: bool = False) -> None:
        post_directory = post.file_path.parent
        storage = post_directory / "archives.json"
        if storage.exists():
            with open(storage) as fp:
                archives = json.load(fp)
        else:
            archives = {}

        # find links from the post HTML
        soup = BeautifulSoup(post.html, "html.parser")
        archived = False
        for el in soup.find_all("a", href=re.compile("http")):
            url = el.attrs["href"]
            if not url or self._safe(url) or url in archives:
                continue

            # save to archive.org
            _logger.info(f"Requesting to save {url}")
            response = requests.get(f"https://web.archive.org/save/{url}")
            content_location = response.headers.get("Content-Location")
            if not content_location:
                continue

            # add link to archived version
            archives[url] = f"https://web.archive.org{content_location}"
            archived = True

        if archived:
            with open(storage, "w") as fp:
                json.dump(archives, fp)

        # now replace links in the generated HTML
        with open(post.file_path.with_suffix(".html")) as fp:
            html = fp.read()
        soup = BeautifulSoup(html, "html.parser")

        # remove any added archive links
        for el in soup.find_all("span", attrs={"class": "archive"}):
            el.decompose()

        modified = False
        for el in soup.find_all("a", href=re.compile("http")):
            if el.attrs["href"] not in archives:
                continue

            archived_url = archives[el.attrs["href"]]
            span = soup.new_tag("span", attrs={"class": "archive"})
            anchor = soup.new_tag("a", href=archived_url)
            anchor.string = "archived"
            span.extend(["[", anchor, "]"])
            el.insert_after(span)
            modified = True

        if modified:
            html = str(soup)
            with open(post.file_path.with_suffix(".html"), "w") as fp:
                fp.write(html)
