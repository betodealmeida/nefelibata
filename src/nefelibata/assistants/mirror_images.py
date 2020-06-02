import hashlib
import mimetypes
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from nefelibata.assistants import Assistant
from nefelibata.assistants import Scope
from nefelibata.post import Post


def get_resource_extension(url: str) -> str:
    response = requests.head(url)
    content_type = response.headers["content-type"]
    extension = mimetypes.guess_extension(content_type)
    return extension or ""


class MirrorImagesAssistant(Assistant):

    scopes = [Scope.POST, Scope.SITE]

    def process_post(self, post: Post) -> None:
        self._process_file(post.file_path.with_suffix(".html"))

    def process_site(self) -> None:
        for path in (self.root / "build").glob("*.html"):
            self._process_file(path)

    def _process_file(self, file_path: Path) -> None:
        mirror = file_path.parent / "img"
        if not mirror.exists():
            mirror.mkdir()

        with open(file_path) as fp:
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
                    fp.write(r.content.decode("utf-8"))

            el.attrs["src"] = "img/%s" % local.name
        html = str(soup)

        with open(file_path, "w") as fp:
            fp.write(html)
