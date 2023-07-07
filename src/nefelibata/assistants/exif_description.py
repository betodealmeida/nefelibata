"""
An assistant that adds EXIF metadata to images.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import marko
import piexif
from marko.renderer import Renderer
from piexif import InvalidImageDataError

from nefelibata.assistants.base import Assistant, Scope
from nefelibata.post import Post

_logger = logging.getLogger(__name__)


def get_image_description(post: Post, path: Path) -> Optional[str]:
    """
    Extract imag edescription from Markdown.
    """
    descriptions: Dict[Path, Optional[str]] = {}

    class DescriptionExtractor(Renderer):
        """
        Pseudo-rendered to extract iamges and their descriptions.
        """

        # pylint: disable=no-self-use
        def render_image(self, element: marko.inline.Image) -> None:
            """
            Store image description.
            """
            parsed = urlparse(element.dest)
            if parsed.netloc == "":
                descriptions[post.path.parent / element.dest] = str(
                    element.children[0].children,
                )

        def render_children(self, element: Any) -> Any:
            if hasattr(element, "children"):
                return [self.render(child) for child in element.children]

            return None

    gemini = marko.Markdown(renderer=DescriptionExtractor)
    gemini.convert(post.content)

    return descriptions.get(path)


class ExifDescriptionAssistant(Assistant):
    """
    Extract image description from Markdown and write as EXIF.
    """

    name = "exif_description"
    scopes = [Scope.POST]

    async def process_post(self, post: Post, force: bool = False) -> None:
        """
        Process post.
        """
        for enclosure in post.enclosures:
            if not enclosure.type.startswith("image/"):
                continue

            description = get_image_description(post, enclosure.path)
            if not description:
                continue

            try:
                exif = piexif.load(str(enclosure.path))
            except InvalidImageDataError:
                _logger.warning("invalid image data in %s", enclosure.path)
                continue

            if exif["0th"].get(piexif.ImageIFD.ImageDescription) == description.encode(
                "utf-8",
            ):
                _logger.info("EXIF description already set in %s", enclosure.path)
                continue

            _logger.info("adding EXIF description to %s", enclosure.path)
            exif["0th"][piexif.ImageIFD.ImageDescription] = description.encode("utf-8")
            piexif.insert(piexif.dump(exif), str(enclosure.path))
