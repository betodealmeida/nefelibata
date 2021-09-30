"""
A builder for Gemini (https://gemini.circumlunar.space/).
"""
import logging
from pathlib import Path
from typing import Any

from md2gemini import md2gemini

from nefelibata.builders.base import Builder
from nefelibata.typing import Config

_logger = logging.getLogger(__name__)


class GeminiBuilder(Builder):

    """
    A builder for the Gemini protocol.
    """

    name = "gemini"
    label = "Gemini"
    extension = ".gmi"
    template_base = ""
    site_templates = ["index.gmi", "feed.gmi"]

    def __init__(  # pylint: disable=too-many-arguments
        self,
        root: Path,
        config: Config,
        home: str,
        path: str = "",
        links: str = "paragraph",
        **kwargs: Any,
    ):
        super().__init__(root, config, home, path, **kwargs)
        self.links = links

        self.setup()

    def render(self, content: str) -> str:
        content = md2gemini(content, links=self.links, plain=True, md_links=True)
        content = content.replace("\r", "")
        return content
