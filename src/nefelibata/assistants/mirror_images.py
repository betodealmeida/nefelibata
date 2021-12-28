"""
Assistant for mirrorring images locally.
"""

import asyncio
import hashlib
import logging
import mimetypes
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from typing import Dict, Iterator, Tuple

import marko
import piexif
from aiohttp import ClientSession
from PIL import Image

from nefelibata.announcers.base import Scope
from nefelibata.assistants.base import Assistant
from nefelibata.post import Post

_logger = logging.getLogger(__name__)

CHUNK_SIZE = 2048


def extract_images(content: str) -> Iterator[Tuple[str, str]]:
    """
    Extract all images from a Markdown document.
    """
    tree = marko.parse(content)
    queue = [tree]
    while queue:
        element = queue.pop()

        if isinstance(element, marko.inline.Image):
            yield element.dest, element.children[0].children
        elif hasattr(element, "children"):
            queue.extend(element.children)


def is_local(url: str) -> bool:
    """
    Return true if the image is local.

    For now we return true if the URL is relative.
    """
    return "://" not in url


async def get_resource_extension(session: ClientSession, url: str) -> str:
    """
    Return the extension of a remote image.
    """
    async with session.head(url) as response:
        content_type = response.headers["content-type"]

    extension = mimetypes.guess_extension(content_type)
    return extension or ""


def get_filename(url: str, extension: str) -> str:
    """
    Compute the filename for a given resource.
    """
    md5 = hashlib.md5()
    md5.update(url.encode("utf-8"))
    return f"{md5.hexdigest()}{extension}"


def add_exif(buf: BytesIO, url: str, title: str) -> BytesIO:
    """
    Store the URL in the EXIF data.
    """
    buf.seek(0)
    image = Image.open(buf)

    exif = (
        piexif.load(image.info["exif"]) if "exif" in image.info else defaultdict(dict)
    )
    exif["0th"][piexif.ImageIFD.Copyright] = url
    exif["0th"][piexif.ImageIFD.ImageDescription] = title

    _logger.info("Adding original URL and title to the EXIF data")
    buf = BytesIO()
    image.save(buf, "jpeg", exif=piexif.dump(exif))

    return buf


async def download_image(  # pylint: disable=too-many-arguments
    session: ClientSession,
    url: str,
    title: str,
    post: Post,
    directory: Path,
    replacements: Dict[str, str],
) -> None:
    """
    Download an image.
    """
    extension = await get_resource_extension(session, url)
    filename = get_filename(url, extension)
    target = directory / filename

    if target.exists():
        _logger.debug("Image already mirrored")
        return

    replacements[url] = str(target.relative_to(post.path.parent))

    _logger.info("Downloading image from %s", url)
    buf = BytesIO()
    async with session.get(url) as response:
        async for chunk in response.content.iter_chunked(  # pragma: no cover
            CHUNK_SIZE,
        ):
            buf.write(chunk)

    if extension in {".jpeg", ".jpg"}:
        buf = add_exif(buf, url, title)

    with open(target, "wb") as output:
        output.write(buf.getvalue())


class MirrorImagesAssistant(Assistant):
    """
    Assistant for mirrorring images locally.
    """

    name = "mirror_images"
    scopes = [Scope.POST]

    async def process_post(self, post: Post, force: bool = False) -> None:
        # create directory for images
        mirror = post.path.parent / "img"
        if not mirror.exists():
            mirror.mkdir()

        replacements: Dict[str, str] = {}
        tasks = []
        async with ClientSession() as session:
            for url, title in extract_images(post.content):
                if is_local(url):
                    continue

                task = asyncio.create_task(
                    download_image(session, url, title, post, mirror, replacements),
                )
                tasks.append(task)

            await asyncio.gather(*tasks)

        if not replacements:
            return

        _logger.info("Updating images in file %s", post.path)
        async with post._lock:  # pylint: disable=protected-access
            with open(post.path, encoding="utf-8") as input_:
                content = input_.read()

            for original, new in replacements.items():
                content = content.replace(original, new)

            with open(post.path, "w", encoding="utf-8") as output:
                output.write(content)
