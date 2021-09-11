import hashlib
import logging
import mimetypes
import re
from collections import defaultdict
from io import BytesIO
from pathlib import Path

import piexif
import requests
from bs4 import BeautifulSoup
from PIL import Image

from nefelibata.assistants import Assistant
from nefelibata.assistants import Scope
from nefelibata.post import Post
from nefelibata.utils import modify_html

_logger = logging.getLogger(__name__)

CHUNK_SIZE = 2048


def get_resource_extension(url: str) -> str:
    response = requests.head(url)
    if "content-type" not in response.headers:
        _logger.warning("No content type found for %s", url)
        return ""
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
        if self.is_path_up_to_date(file_path):
            return

        mirror = file_path.parent / "img"
        if not mirror.exists():
            mirror.mkdir()

        soup: BeautifulSoup
        with modify_html(file_path) as soup:
            external_images = soup.find_all("img", src=re.compile("http"))
            for image in external_images:
                url = image.attrs["src"]

                extension = get_resource_extension(url).lower()
                m = hashlib.md5()
                m.update(url.encode("utf-8"))
                filename = f"{m.hexdigest()}{extension}"
                local = mirror / filename
                image.attrs["src"] = "img/%s" % local.name

                if local.exists():
                    continue

                # download and store locally
                buf = BytesIO()
                response = requests.get(url, stream=True)
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    buf.write(chunk)

                # store original URL in EXIF
                if extension in [".jpeg", ".jpg"]:
                    buf.seek(0)
                    im = Image.open(buf)
                    exif = (
                        piexif.load(im.info["exif"])
                        if "exif" in im.info
                        else defaultdict(dict)
                    )
                    exif["0th"][piexif.ImageIFD.ImageDescription] = url
                    buf = BytesIO()
                    im.save(buf, "jpeg", exif=piexif.dump(exif))

                with open(local, "wb") as outp:
                    outp.write(buf.getvalue())

        self.update_path(file_path)
