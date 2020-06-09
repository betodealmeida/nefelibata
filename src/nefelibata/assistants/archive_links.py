import json
import logging
import re
import urllib.parse
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from pathlib import Path

import dateutil.parser
import requests
from bs4 import BeautifulSoup
from nefelibata.assistants import Assistant
from nefelibata.assistants import Scope
from nefelibata.post import Post

_logger = logging.getLogger(__name__)

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
            if not url or self._safe(url):
                continue

            if url in archives:
                # if the URL has been archived already, skip
                if archives[url]["url"]:
                    continue

                # if the URL has not been archived but we tried
                # recently, skip it to not overload archive.org
                if (
                    datetime.now().astimezone(timezone.utc)
                    - dateutil.parser.parse(archives[url]["date"])
                    < RETRY_TIMEOUT
                ):
                    continue

            # save to archive.org
            _logger.info(f"Requesting to save {url}")
            response = requests.get(f"https://web.archive.org/save/{url}")
            content_location = response.headers.get("Content-Location")
            archived_url = (
                f"https://web.archive.org{content_location}"
                if content_location
                else None
            )

            # add link to archived version
            archives[url] = {
                "url": archived_url,
                "date": datetime.now().astimezone(timezone.utc).isoformat(),
            }
            archived = True

        if archived:
            with open(storage, "w") as fp:
                json.dump(archives, fp)

        # now enrich links in the generated HTML
        index_html = post.file_path.with_suffix(".html")
        with open(index_html) as fp:
            html = fp.read()
        soup = BeautifulSoup(html, "html.parser")

        # remove existing archive notes
        for el in soup.find_all("span", attrs={"class": "archive"}):
            el.decompose()

        modified = False
        for el in soup.find_all("a", href=re.compile("http")):
            url = el.attrs["href"]
            if url not in archives:
                continue

            if el.attrs.get("data-archive-url") != archives[url]["url"]:
                el.attrs["data-archive-url"] = archives[url]["url"]
                el.attrs["data-archive-date"] = archives[url]["date"]

                span = soup.new_tag("span", attrs={"class": "archive"})
                anchor = soup.new_tag("a", href=archives[url]["url"])
                anchor.string = "archived"
                span.extend(["[", anchor, "]"])
                el.insert_after(span)

                modified = True

        if modified:
            html = str(soup)
            with open(index_html, "w") as fp:
                fp.write(html)
