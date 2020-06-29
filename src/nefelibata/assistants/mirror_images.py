import hashlib
import mimetypes
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from nefelibata.assistants import Assistant
from nefelibata.assistants import Scope
from nefelibata.post import Post
from nefelibata.utils import modify_html


CHUNK_SIZE = 2048


def get_resource_extension(url: str) -> str:
    response = requests.head(url)
    content_type = response.headers["content-type"]
    extension = mimetypes.guess_extension(content_type)
    return extension or ""


class MirrorImagesAssistant(Assistant):

    scopes = [Scope.POST, Scope.SITE]

    def process_post(self, post: Post, force: bool = False) -> None:
        self._process_file(post.file_path.with_suffix(".html"))

    def process_site(self, force: bool = False) -> None:
        for path in (self.root / "build").glob("*.html"):
            self._process_file(path)

    def _process_file(self, file_path: Path) -> None:
        mirror = file_path.parent / "img"
        if not mirror.exists():
            mirror.mkdir()

        soup: BeautifulSoup
        with modify_html(file_path) as soup:
            external_images = soup.find_all("img", src=re.compile("http"))
            for image in external_images:
                url = image.attrs["src"]

                extension = get_resource_extension(url)
                m = hashlib.md5()
                m.update(url.encode("utf-8"))
                filename = f"{m.hexdigest()}{extension}"
                local = mirror / filename

                # download and store locally
                if not local.exists():
                    response = requests.get(url, stream=True)
                    with open(local, "wb") as outp:
                        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                            outp.write(chunk)

                image.attrs["src"] = "img/%s" % local.name
