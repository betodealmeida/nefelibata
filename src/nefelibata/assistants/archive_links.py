import logging
import re
import time
import urllib.parse
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any
from typing import Dict
from typing import Optional

import dateutil.parser
import requests
from bs4 import BeautifulSoup

from nefelibata.assistants import Assistant
from nefelibata.assistants import Scope
from nefelibata.post import Post
from nefelibata.utils import json_storage
from nefelibata.utils import modify_html

_logger = logging.getLogger(__name__)

SAVE_TIMEOUT = timedelta(seconds=10)
RETRY_TIMEOUT = timedelta(days=1)


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
        if self.is_path_up_to_date(post.file_path) and not force:
            return

        # store all links to the post directory with information about where and
        # when they were saved, so they can be used by templates
        post_directory = post.file_path.parent
        storage = post_directory / "archives.json"
        archives: Dict[str, Any]
        with json_storage(storage) as archives:
            self._archive_links(post, archives)

        # now enrich links in the generated HTML with the saved link
        index_html = post.file_path.with_suffix(".html")
        soup: BeautifulSoup
        with modify_html(index_html) as soup:
            # remove existing archive notes
            for el in soup.find_all("span", attrs={"class": "archive"}):
                el.decompose()

            for el in soup.find_all("a", href=re.compile("http")):
                url = el.attrs["href"]
                if url not in archives or not archives[url]["url"]:
                    continue

                el.attrs["data-archive-url"] = archives[url]["url"]
                el.attrs["data-archive-date"] = archives[url]["date"]

                span = soup.new_tag("span", attrs={"class": "archive"})
                anchor = soup.new_tag("a", href=archives[url]["url"])
                anchor.string = "archived"
                span.extend(["[", anchor, "]"])
                el.insert_after(span)

        self.update_path(post.file_path)

    def _archive_links(self, post: Post, archives: Dict[str, Any]) -> None:
        # find links from the post HTML
        soup = BeautifulSoup(post.render(self.config), "html.parser")
        for el in soup.find_all("a", href=re.compile("http")):
            url = el.attrs["href"]
            if not url or self._safe(url):
                continue

            if url in archives:
                # if the URL has been archived already, skip
                if archives[url]["url"]:
                    continue

                # if the URL has not been archived but we tried
                # recently, skip it to not overload archive.org
                if (
                    datetime.now(tz=timezone.utc)
                    - dateutil.parser.parse(archives[url]["date"])
                    < RETRY_TIMEOUT
                ):
                    continue

            # save to archive.org
            _logger.info(f"Requesting to save {url}")
            try:
                response = requests.get(
                    f"https://web.archive.org/save/{url}",
                    timeout=SAVE_TIMEOUT.total_seconds(),
                    allow_redirects=True,
                )
            except requests.exceptions.ReadTimeout:
                _logger.info("Request timed out")
                continue

            if response.status_code == 429:
                continue

            archived_url: Optional[str] = None
            link_header = response.headers.get("Link")
            if link_header:
                links = requests.utils.parse_header_links(link_header)
                for link in links:
                    if link["rel"] == "memento":
                        archived_url = link["url"]
                        break

            # add link to archived version
            archives[url] = {
                "url": archived_url,
                "date": datetime.now(tz=timezone.utc).isoformat(),
            }

            # archive.org restricts this to 5 per minute, see
            # https://rationalwiki.org/wiki/Internet_Archive#Restrictions
            time.sleep(12)
