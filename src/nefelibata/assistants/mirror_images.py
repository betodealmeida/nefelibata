import hashlib
import mimetypes
import re
import urllib.parse
from pathlib import Path
from typing import List
from typing import TypedDict

import requests
from bs4 import BeautifulSoup
from nefelibata.assistants import Assistant
from nefelibata.assistants import Scope
from nefelibata.post import Post
from nefelibata.utils import get_config


def get_resource_extension(url: str) -> str:
    response = requests.head(url)
    content_type = response.headers["content-type"]
    extension = mimetypes.guess_extension(content_type)
    return extension or ""


class MirrorImagesAssistant(Assistant):

    scope = [Scope.POST, Scope.SITE]

    def process_post(self, post: Post) -> None:
        mirror = post.file_path.parent / "img"
        if not mirror.exists():
            mirror.mkdir()

        index_html = post.file_path.with_suffix(".html")
        with open(index_html) as fp:
            html = fp.read()

        soup = BeautifulSoup(html, "html.parser")
        for el in soup.find_all("img", src=re.compile("http")):
            url = el.attrs["src"]

            extension = get_resource_extension(url)
            m = hashlib.md5()
            m.update(url.encode("utf-8"))
            filename = f"{m.hexdigest()}{extension}"
            local = mirror / filename

            # download and store locally
            if not local.exists():
                r = requests.get(url)
                with open(local, "w") as fp:
                    fp.write(r.raw)

            el.attrs["src"] = "img/%s" % local.name

        with open(index_html, "w") as fp:
            fp.write(str(soup))
