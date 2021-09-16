"""
A builder for Gemini (https://gemini.circumlunar.space/).
"""
import logging
from pathlib import Path

from md2gemini import md2gemini

from nefelibata.builders.base import Builder, Scope
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

    scopes = [Scope.POST, Scope.SITE]

    def __init__(self, root: Path, config: Config, home: str, links: str = "paragraph"):
        super().__init__(root, config, home)
        self.links = links

        self.setup()

    def render(self, content: str) -> str:
        content = md2gemini(content, links=self.links, plain=True, md_links=True)
        content = content.replace("\r", "")
        return content
